from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (
    urlsafe_base64_decode,
    urlsafe_base64_encode
)
from django.views.generic import CreateView

from .forms import CustomUserCreationForm
from .tokens import email_verification_token


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'

    def form_valid(self, form):
        user = form.save()

        login(self.request, user)

        messages.success(
            self.request,
            'Account created successfully.'
        )

        if user.is_admin_role:
            return redirect('dashboard:admin_dashboard')

        return redirect('dashboard:user_dashboard')


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):

        redirect_url = self.get_redirect_url()

        if redirect_url:
            return redirect_url

        user = self.request.user

        if user.is_admin_role:
            return reverse_lazy(
                'dashboard:admin_dashboard'
            )

        return reverse_lazy(
            'dashboard:user_dashboard'
        )


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')


def verify_email(request, uidb64, token):

    User = get_user_model()

    try:
        uid = force_str(
            urlsafe_base64_decode(uidb64)
        )

        user = User.objects.get(pk=uid)

    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist
    ):
        user = None

    if user and email_verification_token.check_token(
        user,
        token
    ):

        user.is_active = True
        user.save(update_fields=['is_active'])

        messages.success(
            request,
            'Email verified successfully.'
        )

        return redirect('users:login')

    return render(
        request,
        'users/verification_invalid.html',
        status=400
    )

















# from django.contrib import messages
# from django.contrib.auth import login
# from django.contrib.auth import get_user_model
# from django.contrib.auth.views import LoginView, LogoutView
# from django.shortcuts import redirect, render
# from django.template.loader import render_to_string
# from django.urls import reverse, reverse_lazy
# from django.utils.encoding import force_bytes, force_str
# from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
# from django.views.generic import CreateView

# from .forms import CustomUserCreationForm
# from .tokens import email_verification_token


# class RegisterView(CreateView):
#     form_class = CustomUserCreationForm
#     template_name = 'users/register.html'
#     success_url = reverse_lazy('dashboard:user_dashboard')

#     def form_valid(self, form):
#         user = form.save()
#         login(self.request, user)

#         messages.success(
#             self.request,
#             "Account created successfully. Welcome to your dashboard."
#         )
#         return redirect(self.success_url)

#     def send_verification_email(self, user):
#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         token = email_verification_token.make_token(user)

#         verification_url = self.request.build_absolute_uri(
#             reverse('users:verify_email', kwargs={
#                 'uidb64': uid,
#                 'token': token
#             })
#         )

#         subject = "Verify your account"

#         message = render_to_string(
#             'users/email_verification_email.html',
#             {
#                 'user': user,
#                 'verification_url': verification_url
#             }
#         )

#         user.email_user(subject, message)


# class CustomLoginView(LoginView):
#     template_name = 'users/login.html'
#     redirect_authenticated_user = True

#     def get_success_url(self):
#         redirect_url = self.get_redirect_url()
#         if redirect_url:
#             return redirect_url

#         user = self.request.user

#         # optional safety check
#         if not user.is_active:
#             messages.error(self.request, "Please verify your email first.")
#             return reverse_lazy('users:login')

#         if getattr(user, "is_admin_role", False):
#             return reverse_lazy('dashboard:admin_dashboard')

#         return reverse_lazy('dashboard:user_dashboard')


# class CustomLogoutView(LogoutView):
#     next_page = reverse_lazy('users:login')


# def verify_email(request, uidb64, token):
#     User = get_user_model()

#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None

#     if user and email_verification_token.check_token(user, token):
#         user.is_active = True
#         user.save(update_fields=['is_active'])

#         messages.success(request, "Email verified successfully. You can now log in.")
#         return redirect('users:login')

#     return render(request, 'users/verification_invalid.html', status=400)
