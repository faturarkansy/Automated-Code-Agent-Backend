import uuid
from django.db import models
from apps.repositories.models import Repository

class AnalysisRun(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        TESTING = 'TESTING', 'Testing Patch'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey('repositories.Repository', on_delete=models.CASCADE, related_name='analysis_runs')
    commit_hash = models.CharField(max_length=64)
    branch = models.CharField(max_length=100, default='main')
    author = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    vulnerabilities_found = models.IntegerField(default=0)
    vulnerability_details = models.JSONField(default=list, blank=True)
    generated_patch = models.TextField(blank=True, null=True)
    generated_unit_test = models.TextField(blank=True, null=True)
    
    # Field baru untuk mencatat hasil test sandbox & iterasi self-healing
    test_output = models.TextField(blank=True, null=True)
    test_passed = models.BooleanField(default=False)
    retry_count = models.IntegerField(default=0)
    
    execution_time_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.repository.name} - {self.commit_hash[:7]} [{self.status}]"