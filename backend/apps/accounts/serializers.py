from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "display_name", "password")
        read_only_fields = ("id",)

    def create(self, validated):
        return User.objects.create_user(**validated)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "display_name", "is_staff", "is_creator", "created_at")


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login with email + password; also returns a small user summary alongside the tokens."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
