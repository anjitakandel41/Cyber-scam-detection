from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        USER = "user", "User"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )

    @property
    def is_admin_role(self):
        return (
            self.role == self.Role.ADMIN
            or self.is_staff
            or self.is_superuser
        )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class RememberedDeviceQuerySet(models.QuerySet):

    def active(self):
        return self.filter(revoked=False, expires_at__gt=timezone.now())

    def purge_expired(self):
        return self.filter(expires_at__lte=timezone.now()).delete()


class RememberedDevice(models.Model):
    """A browser/device that a user has logged in from and then logged out of.

    This is NOT a login credential. It only lets the browser re-open the owner's
    dashboard in read-only "view mode"; every sensitive action still requires a
    real authenticated session.

    Only the SHA-256 hash of the device token is stored, so a database leak does
    not hand out usable cookies. ``auth_hash`` mirrors Django's session auth hash,
    so changing the password automatically invalidates every remembered device.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='remembered_devices',
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    auth_hash = models.CharField(max_length=128)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    objects = RememberedDeviceQuerySet.as_manager()

    class Meta:
        ordering = ['-last_seen_at']
        verbose_name = 'remembered device'
        verbose_name_plural = 'remembered devices'

    def __str__(self):
        return f"Remembered device for {self.user} (expires {self.expires_at:%Y-%m-%d})"

    @property
    def is_usable(self):
        return not self.revoked and self.expires_at > timezone.now()
