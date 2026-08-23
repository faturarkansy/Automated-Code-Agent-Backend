import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.repositories.models import Repository
from apps.audit_logs.models import AnalysisRun
from apps.audit_logs.services import AnalyticsService

User = get_user_model()

@pytest.mark.django_db
class TestAutomatedAgentPipeline:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="fatur_tester", password="securepassword123")
        self.repo = Repository.objects.create(
            name="Automated-Code-Agent-Backend",
            user=self.user
        )

    def test_webhook_ingestion_success(self):
        """Memastikan endpoint webhook menerima payload valid dan mengembalikan status 202"""
        url = f"/api/v1/repositories/{self.repo.id}/webhook/"
        payload = {
            "commit_hash": "a" * 40,
            "branch": "main",
            "author": "Fatur",
            "code_diff": "def get_data(): return 1"
        }
        with patch("apps.audit_logs.tasks.analyze_code_diff_task.delay") as mock_task:
            response = self.client.post(url, payload, format="json")
            assert response.status_code == 202
            assert response.data["status"] == AnalysisRun.StatusChoices.PENDING
            mock_task.assert_called_once()

    def test_analytics_metrics_calculation(self):
        """Memastikan AnalyticsService mengagregasi data scan dan kalkulasi pass rate dengan tepat"""
        AnalysisRun.objects.create(
            repository=self.repo,
            commit_hash="b" * 40,
            branch="main",
            author="Fatur",
            status=AnalysisRun.StatusChoices.COMPLETED,
            vulnerabilities_found=2,
            vulnerability_details=[{"severity": "HIGH"}, {"severity": "CRITICAL"}],
            test_passed=True,
            execution_time_ms=1200
        )
        metrics = AnalyticsService.get_dashboard_metrics(repository_id=self.repo.id)
        assert metrics["total_scans"] >= 1
        assert metrics["severity_distribution"]["CRITICAL"] >= 1
        assert metrics["severity_distribution"]["HIGH"] >= 1
        assert metrics["test_pass_rate_percentage"] == 100.0