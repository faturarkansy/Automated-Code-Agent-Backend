import json
from django.db.models import Count, Avg, Q, Sum
from django.core.cache import cache
from .models import AnalysisRun
from apps.repositories.models import Repository

class AnalyticsService:
    CACHE_KEY = "dashboard_metrics_summary"
    CACHE_TTL = 60  # Cache selama 60 detik

    @classmethod
    def get_dashboard_metrics(cls, repository_id=None) -> dict:
        cache_key = f"{cls.CACHE_KEY}_{repository_id}" if repository_id else cls.CACHE_KEY
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        qs = AnalysisRun.objects.all()
        if repository_id:
            qs = qs.filter(repository_id=repository_id)

        total_scans = qs.count()
        total_repos = Repository.objects.count() if not repository_id else 1

        if total_scans == 0:
            metrics = {
                "total_repositories": total_repos,
                "total_scans": 0,
                "total_vulnerabilities_found": 0,
                "total_prs_created": 0,
                "test_pass_rate_percentage": 0.0,
                "avg_execution_time_ms": 0.0,
                "severity_distribution": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "status_breakdown": {
                    "PENDING": 0,
                    "IN_PROGRESS": 0,
                    "TESTING": 0,
                    "COMPLETED": 0,
                    "FAILED": 0
                }
            }
            cache.set(cache_key, metrics, timeout=cls.CACHE_TTL)
            return metrics

        # 1. Agregasi Global
        aggregations = qs.aggregate(
            total_vulns=Sum("vulnerabilities_found"),
            avg_exec_time=Avg("execution_time_ms"),
            passed_tests=Count("id", filter=Q(test_passed=True)),
            prs_opened=Count("id", filter=Q(pr_url__isnull=False)),
            completed_runs=Count("id", filter=Q(status=AnalysisRun.StatusChoices.COMPLETED)),
            failed_runs=Count("id", filter=Q(status=AnalysisRun.StatusChoices.FAILED)),
            pending_runs=Count("id", filter=Q(status=AnalysisRun.StatusChoices.PENDING)),
            in_progress_runs=Count("id", filter=Q(status=AnalysisRun.StatusChoices.IN_PROGRESS)),
            testing_runs=Count("id", filter=Q(status=AnalysisRun.StatusChoices.TESTING)),
        )

        # 2. Distribusi Severity Aman (Parsing Robust)
        severity_dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        all_runs = qs.exclude(vulnerability_details=[]).values_list("vulnerability_details", flat=True)
        
        for details in all_runs:
            if not details:
                continue
                
            # Parse jika tersimpan sebagai string JSON
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    continue

            if isinstance(details, list):
                for item in details:
                    if isinstance(item, str):
                        try:
                            item = json.loads(item)
                        except Exception:
                            continue

                    if isinstance(item, dict):
                        sev = str(item.get("severity", "LOW")).upper()
                        if sev in severity_dist:
                            severity_dist[sev] += 1
                        else:
                            severity_dist["LOW"] += 1

        pass_rate = round((aggregations["passed_tests"] / total_scans) * 100, 2) if total_scans > 0 else 0.0
        avg_time = round(aggregations["avg_exec_time"] or 0.0, 2)

        metrics = {
            "total_repositories": total_repos,
            "total_scans": total_scans,
            "total_vulnerabilities_found": aggregations["total_vulns"] or 0,
            "total_prs_created": aggregations["prs_opened"],
            "test_pass_rate_percentage": pass_rate,
            "avg_execution_time_ms": avg_time,
            "severity_distribution": severity_dist,
            "status_breakdown": {
                "PENDING": aggregations["pending_runs"],
                "IN_PROGRESS": aggregations["in_progress_runs"],
                "TESTING": aggregations["testing_runs"],
                "COMPLETED": aggregations["completed_runs"],
                "FAILED": aggregations["failed_runs"],
            }
        }

        cache.set(cache_key, metrics, timeout=cls.CACHE_TTL)
        return metrics