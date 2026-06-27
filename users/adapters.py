from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        email = data.get("email", "")

        if email:
            base_username = email.split("@")[0]
            username = base_username
            count = 1

            while User.objects.filter(username=username).exists():
                username = f"{base_username}{count}"
                count += 1

            user.username = username

        return user