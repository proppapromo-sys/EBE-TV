from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.notifications import email as mailer
from apps.subscriptions.services import subscription_summary
from .serializers import EmailTokenObtainPairSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        mailer.send_welcome(user)                       # best-effort, fail-soft
        return Response({"user": UserSerializer(user).data, **_tokens_for(user)},
                        status=status.HTTP_201_CREATED)


class PasswordResetView(APIView):
    """Email a reset link. Always returns ok so it can't be used to probe which emails exist."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").lower().strip()
        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_BASE_URL}/reset?uid={uid}&token={token}"
            mailer.send_password_reset(user, link)
        return Response({"ok": True})


class PasswordResetConfirmView(APIView):
    """Validate the uid+token and set the new password."""
    permission_classes = [AllowAny]

    def post(self, request):
        uid, token = request.data.get("uid"), request.data.get("token")
        password = request.data.get("password") or ""
        if len(password) < 8:
            return Response({"error": "password_too_short"}, status=400)
        try:
            user = User.objects.get(pk=urlsafe_base64_decode(uid).decode())
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "invalid_link"}, status=400)
        if not default_token_generator.check_token(user, token):
            return Response({"error": "invalid_or_expired"}, status=400)
        user.set_password(password)
        user.save(update_fields=["password"])
        return Response({"ok": True})


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except Exception:
            return Response({"error": "invalid_refresh"}, status=400)
        return Response({"ok": True})


class SocialView(APIView):
    """Apple/Google sign-in token exchange. Stub: verify the provider id_token, then upsert a
    user and return our JWTs. Wire the provider verification before production."""
    permission_classes = [AllowAny]

    def post(self, request):
        provider = request.data.get("provider")
        email = (request.data.get("email") or "").lower().strip()
        if not email:
            return Response({"error": "email_required",
                             "detail": "verify the %s id_token server-side, then pass the email"
                             % provider}, status=400)
        user, _ = User.objects.get_or_create(
            email=email, defaults={"display_name": request.data.get("name", "")})
        return Response({"user": UserSerializer(user).data, **_tokens_for(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": UserSerializer(request.user).data,
                         "subscription": subscription_summary(request.user.id)})
