import uuid
from django.db import models
from apps.repositories.models import Repository

class AnalysisRun(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='analysis_runs')
    commit_hash = models.CharField(max_length=40, db_index=True)
    branch = models.CharField(max_length=100, default='main')
    author = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING,
        db_index=True
    )
    vulnerabilities_found = models.PositiveIntegerField(default=0)
    vulnerability_details = models.JSONField(default=list, blank=True)
    generated_patch = models.TextField(blank=True, null=True)
    generated_unit_test = models.TextField(blank=True, null=True)
    execution_time_ms = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['repository', 'status']),
            models.Index(fields=['commit_hash']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Run {self.commit_hash[:7]} - {self.status}"