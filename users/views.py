from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django.forms.forms import NON_FIELD_ERRORS
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from .forms import CustomUserCreationForm
from .remember import forget_device, is_rememberable

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

    def get_initial(self):
        """Pre-fill the username for a remembered browser (convenience only)."""
        initial = super().get_initial()
        remembered_user = getattr(self.request, 'remembered_user', None)

        if remembered_user is not None:
            initial.setdefault('username', remembered_user.get_username())

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remembered_user'] = getattr(self.request, 'remembered_user', None)
        return context

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

        # RememberedDeviceMiddleware rebinds this browser to the new user on the
        # way out, which also covers Google / allauth logins.
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

    def dispatch(self, request, *args, **kwargs):
        # The device cookie was already minted at login time and survives the
        # session flush, so logging out is what actually switches this browser
        # into view-only mode. Capture the state before the session is cleared.
        was_remembered = (
            request.method == 'POST'
            and request.user.is_authenticated
            and is_rememberable(request.user)
        )

        response = super().dispatch(request, *args, **kwargs)

        if was_remembered:
            messages.info(
                request,
                "You have been logged out. Your dashboard stays available on "
                "this device in view-only mode until you log in again.",
            )

        return response


@require_POST
def forget_device_view(request):
    """"Not you? / Forget this device" - drop the memory and the cookie."""
    response = redirect('home')
    forget_device(request, response)

    messages.success(
        request,
        "This device no longer remembers your dashboard.",
    )

    return response


def home(request):
    """Public landing page.

    A browser that is remembered but has no live session is sent straight to its
    read-only dashboard the first time it opens the site, instead of the login
    page. The one-shot session flag keeps the marketing pages reachable
    afterwards.
    """
    if (
        request.method == 'GET'
        and getattr(request, 'is_view_mode', False)
        and not request.session.get('view_mode_landing_done')
    ):
        request.session['view_mode_landing_done'] = True
        return redirect('dashboard:user_dashboard')

    return render(request, 'home-modern.html')


# REMOVED: verify_email function - no longer needed
# REMOVED: send_verification_email method - no longer needed
