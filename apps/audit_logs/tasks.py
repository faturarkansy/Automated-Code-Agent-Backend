import time
import json
import hashlib
from celery import shared_task
from django.core.cache import cache
from .models import AnalysisRun
from .agent.analyzer import CodeAnalysisAgent
from .agent.sandbox import SandboxRunner
from .agent.github_client import GitHubPRService

@shared_task(bind=True, max_retries=2)
def analyze_code_diff_task(self, analysis_run_id, code_diff):
    try:
        run = AnalysisRun.objects.select_related('repository').get(id=analysis_run_id)
        run.status = AnalysisRun.StatusChoices.IN_PROGRESS
        run.save(update_fields=['status'])

        start_time = time.time()
        agent = CodeAnalysisAgent()

        # 1. Analisis Diff dengan AI
        analysis_result = agent.analyze(code_diff=code_diff)
        patch = analysis_result.patch
        unit_test = analysis_result.unit_test
        vulnerabilities = [v.model_dump() for v in analysis_result.vulnerabilities]

        # 2. Sandbox Testing & Feedback Loop
        run.status = AnalysisRun.StatusChoices.TESTING
        run.save(update_fields=['status'])

        max_iterations = 3
        current_iteration = 0
        test_passed = False
        test_output = ""

        while current_iteration < max_iterations:
            current_iteration += 1
            test_result = SandboxRunner.run_test(patch_code=patch, test_code=unit_test)
            test_passed = test_result["passed"]
            test_output = test_result["output"]

            if test_passed:
                break
            
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

        # 3. Automated Pull Request Creation (Jika Test Passed & Ada Bug)
        pr_url = None
        pr_number = None
        if test_passed and len(vulnerabilities) > 0:
            gh_service = GitHubPRService()
            # Gunakan repo name asli, contoh format: 'owner/repo_name'
            pr_res = gh_service.create_security_pr(
                repo_full_name=run.repository.full_name,
                base_branch=run.branch,
                commit_hash=run.commit_hash,
                vulnerabilities=vulnerabilities,
                patch_code=patch,
                unit_test_code=unit_test,
                test_output=test_output
            )
            if pr_res.get("success"):
                pr_url = pr_res.get("pr_url")
                pr_number = pr_res.get("pr_number")

        execution_time = int((time.time() - start_time) * 1000)

        # 4. Simpan Record ke Database
        run.status = AnalysisRun.StatusChoices.COMPLETED
        run.vulnerabilities_found = len(vulnerabilities)
        run.vulnerability_details = vulnerabilities
        run.generated_patch = patch
        run.generated_unit_test = unit_test
        run.test_passed = test_passed
        run.test_output = test_output
        run.retry_count = current_iteration - 1
        run.pr_url = pr_url
        run.pr_number = pr_number
        run.execution_time_ms = execution_time
        run.save()

        return f"Analysis {analysis_run_id} completed. PR Created: {pr_url}"

    except Exception as exc:
        run = AnalysisRun.objects.filter(id=analysis_run_id).first()
        if run:
            run.status = AnalysisRun.StatusChoices.FAILED
            run.save(update_fields=['status'])
        raise self.retry(exc=exc, countdown=5)