from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic import CreateView

from .forms import CustomUserCreationForm
from .tokens import email_verification_token

from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "users/register.html"

    def form_valid(self, form):
        user = form.save()

        # Optional: require email verification
        user.is_active = False
        user.save()

        self.send_verification_email(user)

        messages.success(
            self.request,
            "Registration successful. Please check your email to verify your account."
        )

        return redirect("users:login")

    def send_verification_email(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)

        verification_url = self.request.build_absolute_uri(
            reverse(
                "users:verify_email",
                kwargs={
                    "uidb64": uid,
                    "token": token,
                },
            )
        )

        subject = "Verify your AI Scam Detection account"

        message = render_to_string(
            "users/email_verification_email.html",
            {
                "user": user,
                "verification_url": verification_url,
            },
        )

        user.email_user(subject, message)

class CustomLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Welcome back, {form.get_user().username}!"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Invalid username or password."
        )
        return super().form_invalid(form)

    def get_success_url(self):

        redirect_url = self.get_redirect_url()

        if redirect_url:
            return redirect_url

        user = self.request.user

        if user.is_admin_role:
            return reverse_lazy("dashboard:admin_dashboard")

        return reverse_lazy("dashboard:user_dashboard")


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("users:login")


def verify_email(request, uidb64, token):

    User = get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
    ):
        user = None

    if user and email_verification_token.check_token(user, token):

        user.is_active = True
        user.save(update_fields=["is_active"])

        messages.success(
            request,
            "Email verified successfully. Please login."
        )

        return redirect("users:login")

    return render(
        request,
        "users/verification_invalid.html",
        status=400,
    )