"""Device-memory helpers behind the "Remember Dashboard" (view mode) feature.

Flow
----
1. A user logs in normally -> a real Django session exists -> full access.
2. The user logs out. Before the session is flushed we mint a random device
   token, store only its SHA-256 hash against the user, and drop a *signed*,
   HttpOnly cookie on the browser.
3. The user later re-opens the site with no session. The middleware resolves the
   cookie back to that user and puts the request into read-only "view mode":
   ``request.user`` stays AnonymousUser, but ``request.display_user`` points at
   the remembered account so read-only pages can render their data.

Security notes
--------------
* The cookie is never a login. ``request.user.is_authenticated`` stays False, so
  anything guarded by ``login_required`` keeps rejecting the visitor.
* The cookie value is signed with SECRET_KEY, and the token itself is random and
  only stored hashed, so it cannot be forged or replayed from a DB dump.
* ``auth_hash`` mirrors ``user.get_session_auth_hash()``. A password change
  rotates it and every remembered device on every browser stops resolving.
* Admin/staff accounts are never remembered.
"""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone
from django.utils.crypto import constant_time_compare

from .models import RememberedDevice

COOKIE_SALT = 'users.remembered_device.v1'

# How long a request may go before we bother writing last_seen_at again.
LAST_SEEN_THROTTLE = timedelta(hours=1)


def cookie_name():
    return getattr(settings, 'REMEMBERED_DEVICE_COOKIE_NAME', 'csd_remembered_device')


def cookie_max_age():
    return getattr(settings, 'REMEMBERED_DEVICE_MAX_AGE', 60 * 60 * 24 * 30)


def view_mode_enabled():
    return getattr(settings, 'VIEW_MODE_ENABLED', True)


def hash_token(raw_token):
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def is_rememberable(user):
    """Only ordinary, active, non-privileged accounts may be remembered."""
    return bool(
        user is not None
        and getattr(user, 'is_authenticated', False)
        and user.is_active
        and not getattr(user, 'is_admin_role', False)
    )


def get_display_user(request):
    """The account whose data a read-only page should render.

    Falls back to ``request.user`` so views stay safe even if the middleware is
    not installed (e.g. in isolated unit tests).
    """
    return getattr(request, 'display_user', None) or request.user


# ---------------------------------------------------------------------------
# Cookie <-> device record
# ---------------------------------------------------------------------------

def _read_raw_token(request):
    value = request.COOKIES.get(cookie_name())

    if not value:
        return None

    try:
        return signing.loads(value, salt=COOKIE_SALT, max_age=cookie_max_age())
    except signing.BadSignature:
        return None


def resolve_remembered_device(request):
    """Return the valid ``RememberedDevice`` for this browser, or ``None``."""
    raw_token = _read_raw_token(request)

    if not raw_token:
        return None

    device = (
        RememberedDevice.objects
        .select_related('user')
        .filter(token_hash=hash_token(raw_token))
        .first()
    )

    if device is None or not device.is_usable:
        return None

    if not is_rememberable(device.user):
        return None

    # Password change (or any credential rotation) invalidates the memory.
    if not constant_time_compare(device.auth_hash, device.user.get_session_auth_hash()):
        return None

    return device


def touch_device(device):
    """Record activity, but at most once per LAST_SEEN_THROTTLE window."""
    now = timezone.now()

    if now - device.last_seen_at >= LAST_SEEN_THROTTLE:
        device.last_seen_at = now
        device.save(update_fields=['last_seen_at'])


def remember_device(request, response, user):
    """Bind this browser to ``user`` and set the signed cookie on ``response``."""
    if not view_mode_enabled() or not is_rememberable(user):
        forget_device(request, response)
        return None

    # Retire whatever this browser was remembering before.
    _revoke_current_device(request)

    raw_token = secrets.token_urlsafe(32)

    device = RememberedDevice.objects.create(
        user=user,
        token_hash=hash_token(raw_token),
        auth_hash=user.get_session_auth_hash(),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        expires_at=timezone.now() + timedelta(seconds=cookie_max_age()),
    )

    RememberedDevice.objects.purge_expired()

    response.set_cookie(
        cookie_name(),
        signing.dumps(raw_token, salt=COOKIE_SALT),
        max_age=cookie_max_age(),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
    )

    return device


def forget_device(request, response):
    """Revoke this browser's memory and clear the cookie."""
    _revoke_current_device(request)
    response.delete_cookie(cookie_name(), samesite='Lax')


def _revoke_current_device(request):
    raw_token = _read_raw_token(request)

    if raw_token:
        RememberedDevice.objects.filter(token_hash=hash_token(raw_token)).delete()
