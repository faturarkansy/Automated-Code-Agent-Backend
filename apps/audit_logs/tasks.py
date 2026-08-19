import time
import json
import hashlib
from celery import shared_task
from django.core.cache import cache
from .models import AnalysisRun
from .agent.analyzer import CodeAnalysisAgent
from .agent.sandbox import SandboxRunner

@shared_task(bind=True, max_retries=2)
def analyze_code_diff_task(self, analysis_run_id, code_diff):
    try:
        run = AnalysisRun.objects.get(id=analysis_run_id)
        run.status = AnalysisRun.StatusChoices.IN_PROGRESS
        run.save(update_fields=['status'])

        start_time = time.time()
        agent = CodeAnalysisAgent()

        # 1. Analisis Awal dengan LLM
        analysis_result = agent.analyze(code_diff=code_diff)
        
        patch = analysis_result.patch
        unit_test = analysis_result.unit_test
        vulnerabilities = [v.model_dump() for v in analysis_result.vulnerabilities]

        # 2. Automated Sandbox Testing & Feedback Loop
        run.status = AnalysisRun.StatusChoices.TESTING
        run.save(update_fields=['status'])

        max_iterations = 3
        current_iteration = 0
        test_passed = False
        test_output = ""

        while current_iteration < max_iterations:
            current_iteration += 1
            # Eksekusi pytest di temporary sandbox
            test_result = SandboxRunner.run_test(patch_code=patch, test_code=unit_test)
            test_passed = test_result["passed"]
            test_output = test_result["output"]

            if test_passed:
                break
            
            # Jika gagal dan masih ada jatah retry, picu perbaikan mandiri (Self-Healing)
            if current_iteration < max_iterations:
                corrected_result = agent.fix_patch_and_test(
                    original_diff=code_diff,
                    current_patch=patch,
                    current_test=unit_test,
                    error_log=test_output
                )
                patch = corrected_result.patch
                unit_test = corrected_result.unit_test
                if corrected_result.vulnerabilities:
                    vulnerabilities = [v.model_dump() for v in corrected_result.vulnerabilities]

        execution_time = int((time.time() - start_time) * 1000)

        # 3. Simpan Hasil Lengkap ke Database
        run.status = AnalysisRun.StatusChoices.COMPLETED
        run.vulnerabilities_found = len(vulnerabilities)
        run.vulnerability_details = vulnerabilities
        run.generated_patch = patch
        run.generated_unit_test = unit_test
        run.test_passed = test_passed
        run.test_output = test_output
        run.retry_count = current_iteration - 1
        run.execution_time_ms = execution_time
        run.save()

        return f"Analysis {analysis_run_id} completed with test_passed={test_passed} in {current_iteration} iteration(s)."

    except Exception as exc:
        run = AnalysisRun.objects.filter(id=analysis_run_id).first()
        if run:
            run.status = AnalysisRun.StatusChoices.FAILED
            run.save(update_fields=['status'])
        raise self.retry(exc=exc, countdown=5)