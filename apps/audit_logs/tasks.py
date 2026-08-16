import time
import json
import hashlib
from celery import shared_task
from django.core.cache import cache
from .models import AnalysisRun

@shared_task(bind=True, max_retries=3)
def analyze_code_diff_task(self, analysis_run_id, code_diff):
    try:
        run = AnalysisRun.objects.get(id=analysis_run_id)
        run.status = AnalysisRun.StatusChoices.IN_PROGRESS
        run.save(update_fields=['status'])

        start_time = time.time()

        # 1. Cek Redis Cache (Semantic/Diff Hash Caching)
        diff_hash = hashlib.sha256(code_diff.encode()).hexdigest()
        cache_key = f"audit_cache:{diff_hash}"
        cached_result = cache.get(cache_key)

        if cached_result:
            result = json.loads(cached_result)
        else:
            # Simulasi AI processing time (sebelum dihubungkan ke LLM di Hari ke-4)
            time.sleep(3)
            result = {
                "vulnerabilities": ["Unvalidated user input in query param", "Potential SQL Injection"],
                "patch": "# Sanitized query input implementation",
                "unit_test": "def test_safe_query(): assert True"
            }
            # Simpan ke Redis cache selama 24 jam (86400 detik)
            cache.set(cache_key, json.dumps(result), timeout=86400)

        execution_time = int((time.time() - start_time) * 1000)

        # 2. Update Database Record
        run.status = AnalysisRun.StatusChoices.COMPLETED
        run.vulnerabilities_found = len(result["vulnerabilities"])
        run.vulnerability_details = result["vulnerabilities"]
        run.generated_patch = result["patch"]
        run.generated_unit_test = result["unit_test"]
        run.execution_time_ms = execution_time
        run.save()

        return f"Analysis {analysis_run_id} completed successfully."

    except Exception as exc:
        run = AnalysisRun.objects.filter(id=analysis_run_id).first()
        if run:
            run.status = AnalysisRun.StatusChoices.FAILED
            run.save(update_fields=['status'])
        raise self.retry(exc=exc, countdown=5)