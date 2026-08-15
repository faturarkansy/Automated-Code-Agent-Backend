import uuid
from django.db import models
from django.contrib.auth.models import User

class Repository(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositories')
    name = models.CharField(max_length=255)
    clone_url = models.URLField(max_length=500)
    access_token = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Repositories"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"