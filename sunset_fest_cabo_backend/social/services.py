# services.py
from django.conf import settings
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from urllib.parse import urlencode
from typing import Dict, Any
import requests
import jwt
from django.contrib.auth import get_user_model

User = get_user_model()

GOOGLE_ACCESS_TOKEN_OBTAIN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
LOGIN_URL = f"{settings.BACKEND_URL}/api/accounts/login"


# Exchange authorization token with access token
def google_get_access_token(code: str, redirect_uri: str) -> str:
    data = {
        "code": code,
        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
    if not response.ok:
        print("RESPONSE", response.json())
        raise ValidationError("Could not get access token from Google.")

    access_token = response.json()["access_token"]

    return access_token


# Get user info from google
def google_get_user_info(access_token: str) -> Dict[str, Any]:
    response = requests.get(GOOGLE_USER_INFO_URL, params={"access_token": access_token})

    if not response.ok:
        raise ValidationError("Could not get user info from Google.")

    return response.json()


def get_user_data(validated_data):
    domain = settings.BACKEND_URL
    redirect_uri = f"{domain}/api/social/login/google/"

    code = validated_data.get("code")
    error = validated_data.get("error")

    if error or not code:
        params = urlencode({"error": error})
        return redirect(f"{LOGIN_URL}?{params}")

    access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)
    user_data = google_get_user_info(access_token=access_token)

    # Creates user in DB if first time login
    User.objects.get_or_create(
        username=user_data["email"],
        email=user_data["email"],
        first_name=user_data.get("given_name") + " " + user_data.get("family_name"),
    )

    profile_data = {
        "email": user_data["email"],
        "first_name": user_data.get("given_name"),
        "last_name": user_data.get("family_name"),
    }
    return profile_data


FACEBOOK_ACCESS_TOKEN_OBTAIN_URL = "https://graph.facebook.com/v12.0/oauth/access_token"
FACEBOOK_USER_INFO_URL = "https://graph.facebook.com/me/"


def facebook_get_access_token(code: str, redirect_uri: str) -> str:
    params = {
        "client_id": settings.FACEBOOK_OAUTH2_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "client_secret": settings.FACEBOOK_OAUTH2_CLIENT_SECRET,
        "code": code,
    }

    response = requests.get(FACEBOOK_ACCESS_TOKEN_OBTAIN_URL, params=params)

    print("FACEBOOK RESPONSE ACCESS TOKEN", response.json())
    if not response.ok:
        raise ValidationError("Could not get access token from Facebook.")

    return response.json().get("access_token")


def facebook_get_user_info(access_token: str) -> Dict[str, Any]:
    response = requests.get(
        FACEBOOK_USER_INFO_URL, params={"access_token": access_token}
    )
    print("FACEBOOK RESPONSE", response.json())

    if not response.ok:
        raise ValidationError("Could not get user info from Facebook.")

    return response.json()


def facebook_get_user_email(user_id: str, access_token: str) -> str:
    response = requests.get(
        f"https://graph.facebook.com/{user_id}",
        params={"access_token": access_token, "fields": "email,name"},
    )
    print("FACEBOOK RESPONSE EMAIL", response.json())

    return response.json()


def get_facebook_user_data(validated_data):
    domain = settings.BACKEND_URL
    redirect_uri = f"{domain}/api/social/login/facebook/"

    code = validated_data.get("code")
    error = validated_data.get("error")

    if error or not code:
        params = urlencode({"error": error})
        return redirect(f"{LOGIN_URL}?{params}")

    access_token = facebook_get_access_token(code=code, redirect_uri=redirect_uri)
    user_data = facebook_get_user_info(access_token=access_token)
    user_email = facebook_get_user_email(
        user_id=user_data.get("id"), access_token=access_token
    )

    # Creates user in DB if first time login
    User.objects.get_or_create(
        username=user_email["email"],
        email=user_email["email"],
        first_name=user_email.get("name"),
    )

    profile_data = {
        "email": user_email["email"],
        "first_name": user_email.get("name"),
    }

    return profile_data
