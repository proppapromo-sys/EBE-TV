from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
        return Response({"user": UserSerializer(user).data, **_tokens_for(user)},
                        status=status.HTTP_201_CREATED)


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
