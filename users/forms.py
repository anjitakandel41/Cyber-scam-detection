from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
                "autocomplete": "email",
            }
        ),
    )

    # Only allow USER registration
    role = forms.ChoiceField(
        label="Account Type",
        choices=[
            (CustomUser.Role.USER, "User"),
        ],
        initial=CustomUser.Role.USER,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "role",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter your username",
            "autocomplete": "username",
        })

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Create a strong password",
            "autocomplete": "new-password",
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm your password",
            "autocomplete": "new-password",
        })

    def clean_email(self):
        email = self.cleaned_data["email"]

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_username(self):
        username = self.cleaned_data["username"]

        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]

        # Prevent privilege escalation
        user.role = CustomUser.Role.USER

        user.is_active = True

        if commit:
            user.save()

        return user