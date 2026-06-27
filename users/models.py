from django.contrib.auth.models import AbstractUser
from django.db import models


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