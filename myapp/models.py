from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserActivity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activity')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_logout = models.DateTimeField(null=True, blank=True)
    is_logged_in = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Activity"

    class Meta:
        verbose_name_plural = "User Activities"
