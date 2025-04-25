from .services import get_user_data, get_facebook_user_data
from django.shortcuts import redirect
from django.conf import settings
from rest_framework.views import APIView
from .serializers import AuthSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class GoogleLoginApi(APIView):
    def get(self, request, *args, **kwargs):
        auth_serializer = AuthSerializer(data=request.GET)
        auth_serializer.is_valid(raise_exception=True)

        validated_data = auth_serializer.validated_data
        user_data = get_user_data(validated_data)

        user = User.objects.get(email=user_data["email"])

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Add token to redirect URL - now pointing to the specific callback endpoint
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/google/callback?token={access_token}"
        )
        return redirect(redirect_url)


class FacebookLoginApi(APIView):
    def get(self, request, *args, **kwargs):
        auth_serializer = AuthSerializer(data=request.GET)
        auth_serializer.is_valid(raise_exception=True)

        validated_data = auth_serializer.validated_data
        user_data = get_facebook_user_data(validated_data)

        user = User.objects.get(email=user_data["email"])

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/facebook/callback?token={access_token}"
        )
        return redirect(redirect_url)
