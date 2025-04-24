from django.urls import path
from .views import GoogleLoginApi

urlpatterns = [
    path('login/google/', GoogleLoginApi.as_view(), name='google_login'),
]
