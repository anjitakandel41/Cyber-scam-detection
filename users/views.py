from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django.forms.forms import NON_FIELD_ERRORS
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomUserCreationForm

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "users/register.html"

    def form_valid(self, form):
        user = form.save()
        
        # User is already active (is_active = True from the form)
        # No email verification needed
        
        messages.success(
            self.request,
            f"Registration successful! Welcome {user.username}! You can now log in."
        )
        
        # Option 1: Redirect to login page (recommended)
        return redirect("users:login")
        
        # Option 2: Auto-login user (uncomment if you want this)
        # login(self.request, user)
        # return redirect("dashboard:user_dashboard")

    def form_invalid(self, form):
        # Display form errors as messages
        for field, errors in form.errors.items():
            for error in errors:
                if field != '__all__':
                    messages.error(self.request, f"{field.replace('_', ' ').title()}: {error}")
                else:
                    messages.error(self.request, error)
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        
        # Check if user is active (should always be true now)
        if not user.is_active:
            messages.error(
                self.request,
                "Your account is not active. Please contact support."
            )
            return render(self.request, self.template_name, {
                'form': form,
                'error': 'Account not active'
            })
        
        messages.success(
            self.request,
            f"Welcome back, {user.username}!"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        # Clear any existing non-field errors
        if NON_FIELD_ERRORS in form._errors:
            del form._errors[NON_FIELD_ERRORS]
        
        # Add custom error message
        form.add_error(None, "Invalid username or password. Please try again.")
        
        # Display errors as messages
        for field, errors in form.errors.items():
            for error in errors:
                if field != '__all__':
                    messages.error(self.request, f"{field}: {error}")
                else:
                    messages.error(self.request, error)
        
        return super().form_invalid(form)

    def get_success_url(self):
        redirect_url = self.get_redirect_url()

        if redirect_url:
            return redirect_url

        user = self.request.user

        if hasattr(user, 'is_admin_role') and user.is_admin_role:
            return reverse_lazy("dashboard:admin_dashboard")

        return reverse_lazy("dashboard:user_dashboard")


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("users:login")


# REMOVED: verify_email function - no longer needed
# REMOVED: send_verification_email method - no longer needed