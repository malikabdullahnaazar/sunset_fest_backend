from django.contrib import admin
from accounts.models import CustomUser, VerificationToken, PasswordResetToken

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'is_subscribed', 'is_completed', 'theme')
    list_filter = ('is_subscribed', 'is_completed', 'theme')
    search_fields = ('email', 'username')

class VerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')

class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')

# Register your models here.
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(VerificationToken, VerificationTokenAdmin)
admin.site.register(PasswordResetToken, PasswordResetTokenAdmin)