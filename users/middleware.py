"""Middleware that puts a remembered browser into read-only "view mode".

Must be listed AFTER ``django.contrib.auth.middleware.AuthenticationMiddleware``
so that ``request.user`` is already available.

Two jobs:

1. **Authenticated request** -- make sure this browser is bound to the logged-in
   user, so that after logout (or session expiry) the dashboard stays reachable
   read-only. Doing it here rather than in the logout view means *every* login
   path is covered, including Google / allauth social login.
2. **Anonymous request with a device cookie** -- resolve the cookie back to its
   owner and flag the request as view mode.

Guarantees:
* It never touches ``request.user`` -- an unauthenticated visitor stays
  unauthenticated, so ``login_required`` and friends behave exactly as before.
* It only hits the database when the device cookie is present or the session has
  not been synced yet, so normal traffic pays no extra cost.
"""

from .remember import (
    cookie_name,
    forget_device,
    remember_device,
    resolve_remembered_device,
    touch_device,
    view_mode_enabled,
)

# Session flag: this browser has already been bound to the logged-in user, so we
# do not re-check on every request of the session.
DEVICE_SYNCED_KEY = '_remembered_device_synced'


class RememberedDeviceMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Safe defaults for every request, so views/templates can rely on them.
        request.is_view_mode = False
        request.remembered_user = None
        request.remembered_device = None
        request.display_user = request.user  # stays lazy until something reads it

        stale_cookie = False

        if (
            view_mode_enabled()
            and not request.user.is_authenticated
            and cookie_name() in request.COOKIES
        ):
            device = resolve_remembered_device(request)

            if device is None:
                stale_cookie = True
            else:
                touch_device(device)
                request.remembered_device = device
                request.remembered_user = device.user
                request.display_user = device.user
                request.is_view_mode = True

        response = self.get_response(request)

        if not view_mode_enabled():
            return response

        # Checked *after* the view so that the login request itself -- where the
        # user only becomes authenticated part-way through -- is covered too.
        # The session flag keeps this to one database write per login.
        if request.user.is_authenticated and not request.session.get(DEVICE_SYNCED_KEY):
            # Rebinds the browser to whoever is logged in now, so one device
            # never remembers two accounts. Admins are dropped, not remembered.
            remember_device(request, response, request.user)
            request.session[DEVICE_SYNCED_KEY] = True

        elif stale_cookie:
            # Expired, revoked, or tampered-with cookie: clean it off the browser.
            forget_device(request, response)

        return response
