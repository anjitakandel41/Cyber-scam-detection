from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse

# Message shown when a remembered (view-mode) visitor touches a restricted feature.
VIEW_MODE_MESSAGE = "Please log in again to perform security scans."

# View mode is strictly read-only: only these methods may reach a view.
SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS'})


def _login_redirect(request, message=None):
    """Send the visitor to the login page, explaining why when in view mode."""
    if message and getattr(request, 'is_view_mode', False):
        messages.warning(request, message)

    return redirect_to_login(request.get_full_path(), reverse('users:login'))


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse('users:login'))
        if not request.user.is_admin_role:
            return redirect('dashboard:user_dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def user_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse('users:login'))
        if request.user.is_admin_role:
            return redirect('dashboard:admin_dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def view_mode_allowed(view_func):
    """Read-only page: full sessions, plus remembered browsers in view mode.

    In view mode only safe HTTP methods are let through, so a decorated view can
    never write data on behalf of a visitor who is not actually logged in. The
    view must read ``users.remember.get_display_user(request)`` rather than
    ``request.user`` to know whose data to render.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        if getattr(request, 'is_view_mode', False):
            if request.method not in SAFE_METHODS:
                return _login_redirect(request, VIEW_MODE_MESSAGE)
            return view_func(request, *args, **kwargs)

        return _login_redirect(request)

    wrapper.view_mode_allowed = True
    return wrapper


def user_or_view_mode_required(view_func):
    """Like :func:`user_required`, but also serves remembered browsers read-only.

    Remembered devices are never created for admin/staff accounts, so view mode
    can only ever reach the ordinary user dashboard.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_admin_role:
                return redirect('dashboard:admin_dashboard')
            return view_func(request, *args, **kwargs)

        if getattr(request, 'is_view_mode', False):
            if request.method not in SAFE_METHODS:
                return _login_redirect(request, VIEW_MODE_MESSAGE)
            return view_func(request, *args, **kwargs)

        return _login_redirect(request)

    wrapper.view_mode_allowed = True
    return wrapper


def session_required(message=VIEW_MODE_MESSAGE):
    """Guard for security-sensitive features (scans, reports, deletes, settings).

    A valid authenticated session is always required. A remembered browser gets
    bounced to the login page with an explanation instead of a silent redirect.

    Usable bare (``@session_required``) or with a custom message
    (``@session_required("...")``).
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            return _login_redirect(request, message)

        wrapper.session_required = True
        return wrapper

    # Support the bare @session_required form.
    if callable(message):
        view_func, message = message, VIEW_MODE_MESSAGE
        return decorator(view_func)

    return decorator
