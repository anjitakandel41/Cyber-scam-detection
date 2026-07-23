from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
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

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter your username",
            "autocomplete": "username",
            "minlength": "3",
        })
        self.fields["username"].help_text = "Required. 3-150 characters. Letters, digits and @/./+/-/_ only."

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Create a strong password (min 8 characters)",
            "autocomplete": "new-password",
        })
        self.fields["password1"].help_text = "Your password must contain at least 8 characters."

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm your password",
            "autocomplete": "new-password",
        })

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken. Please choose another one."
            )

        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        if len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)

        # Set email (already cleaned)
        user.email = self.cleaned_data["email"]

        # Always set role to USER
        user.role = CustomUser.Role.USER

        # User is active immediately (no email verification)
        user.is_active = True

        if commit:
            user.save()

        return user