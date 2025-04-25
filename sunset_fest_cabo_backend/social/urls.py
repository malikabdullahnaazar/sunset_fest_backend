from django.urls import path
from .views import GoogleLoginApi, FacebookLoginApi

urlpatterns = [
    path("login/google/", GoogleLoginApi.as_view(), name="google_login"),
    path("login/facebook/", FacebookLoginApi.as_view(), name="facebook_login"),
]
