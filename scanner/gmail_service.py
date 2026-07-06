from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from allauth.socialaccount.models import SocialToken


def get_gmail_service(user):
    social_token = SocialToken.objects.filter(account__user=user).first()

    if not social_token:
        raise Exception("Google account not connected.")

    credentials = Credentials(
        token=social_token.token,
        refresh_token=social_token.token_secret,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
        ],
    )

    service = build("gmail", "v1", credentials=credentials)

    return service