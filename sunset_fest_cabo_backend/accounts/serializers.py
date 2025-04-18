from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import uuid
from .models import CustomUser, PasswordResetToken ,VerificationToken

# Registration serializer with verification token
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'image']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email'],
            image=validated_data.get('image', None),
            is_active=False  # User starts inactive
        )
        user.set_password(validated_data['password'])
        user.save()

        # Create a verification token
        verification_token = VerificationToken.objects.create(user=user)

        print(verification_token.token)
        print(settings.FRONTEND_URL)

        rest_url = f"verify-email/{verification_token.token}/"
        # Send verification email
        verification_url = f"{settings.FRONTEND_URL}/{rest_url}"
        send_mail(
            subject='Verify Your Email',
            message=f'Click the link to verify your email: {verification_url}\nThis link expires in 24 hours.',
            from_email=settings.FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user
# Login serializer with email and is_active check
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_subscribed':user.is_subscribed,
            'theme':user.theme,
            'is_completed':user.is_completed,
            'image': user.image.url if user.image else None  # Return image URL if exists
        }
        if not user.check_password(credentials['password']):
            raise serializers.ValidationError('Incorrect password.')
        if not user:
            raise serializers.ValidationError('No user found with this email.')
        if not user.is_active:
            raise serializers.ValidationError('Account not verified. Please check your email.')
        return data
# Forgot password serializer
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('No user found with this email.')
        return value

    def save(self):
        email = self.validated_data['email']
        user = CustomUser.objects.get(email=email)
        
        # Create a new reset token
        reset_token = PasswordResetToken.objects.create(user=user)

        token_url = f"reset-password/{reset_token.token}/"

        # Send reset email
        reset_url = f"{settings.FRONTEND_URL}/{token_url}"
        
        # Send reset email
        #reset_url = f"{settings.FRONTEND_URL}{reverse('reset_password', args=[str(reset_token.token)])}"
        send_mail(
            subject='Reset Your Password',
            message=f'Click the link to reset your password: {reset_url}\nThis link expires in 1 hour.',
            from_email='no-reply@yourdomain.com',
            recipient_list=[user.email],
            fail_silently=False,
        )

# Reset password serializer
class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
            if not reset_token.is_valid():
                raise serializers.ValidationError('Token is invalid, expired, or already used.')
            return value
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Invalid token.')

    def save(self):
        token = self.validated_data['token']
        reset_token = PasswordResetToken.objects.get(token=token)
        user = reset_token.user
        user.set_password(self.validated_data['password'])
        user.save()
        
        # Mark token as used
        reset_token.is_used = True
        reset_token.save()
