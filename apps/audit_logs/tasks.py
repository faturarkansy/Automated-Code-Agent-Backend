import time
import json
import hashlib
from celery import shared_task
from django.core.cache import cache
from .models import AnalysisRun
from .agent.analyzer import CodeAnalysisAgent

@shared_task(bind=True, max_retries=2)
def analyze_code_diff_task(self, analysis_run_id, code_diff):
    try:
        run = AnalysisRun.objects.get(id=analysis_run_id)
        run.status = AnalysisRun.StatusChoices.IN_PROGRESS
        run.save(update_fields=['status'])

        start_time = time.time()

        # 1. Cek Redis Cache
        diff_hash = hashlib.sha256(code_diff.encode()).hexdigest()
        cache_key = f"audit_cache:{diff_hash}"
        cached_data = cache.get(cache_key)

        if cached_data:
            result_dict = json.loads(cached_data)
        else:
            # 2. Panggil AI Agent Sungguhan
            agent = CodeAnalysisAgent()
            analysis_result = agent.analyze(code_diff=code_diff)
            
            # Serialize Pydantic object ke dict
            result_dict = {
                "vulnerabilities": [v.model_dump() for v in analysis_result.vulnerabilities],
                "patch": analysis_result.patch,
                "unit_test": analysis_result.unit_test
            }
            
            # Simpan hasil analisis AI ke Redis cache (24 jam)
            cache.set(cache_key, json.dumps(result_dict), timeout=86400)

        execution_time = int((time.time() - start_time) * 1000)

        # 3. Update Status & Hasil ke PostgreSQL
        run.status = AnalysisRun.StatusChoices.COMPLETED
        run.vulnerabilities_found = len(result_dict["vulnerabilities"])
        run.vulnerability_details = result_dict["vulnerabilities"]
        run.generated_patch = result_dict["patch"]
        run.generated_unit_test = result_dict["unit_test"]
        run.execution_time_ms = execution_time
        run.save()

        return f"Analysis {analysis_run_id} finished by AI Agent in {execution_time}ms"

    except Exception as exc:
        run = AnalysisRun.objects.filter(id=analysis_run_id).first()
        if run:
            run.status = AnalysisRun.StatusChoices.FAILED
            run.save(update_fields=['status'])
        raise self.retry(exc=exc, countdown=5)