import tempfile
import subprocess
import os

class SandboxRunner:
    @staticmethod
    def run_test(patch_code: str, test_code: str, timeout_seconds: int = 10) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file_path = os.path.join(temp_dir, "solution.py")
            test_file_path = os.path.join(temp_dir, "test_solution.py")

            # Bersihkan blok markdown jika ada
            clean_patch = patch_code
            if "```python" in patch_code:
                clean_patch = patch_code.split("```python")[1].split("```")[0]
            elif "```" in patch_code:
                clean_patch = patch_code.split("```")[1].split("```")[0]

            clean_test = test_code
            if "```python" in test_code:
                clean_test = test_code.split("```python")[1].split("```")[0]
            elif "```" in test_code:
                clean_test = test_code.split("```")[1].split("```")[0]

            with open(src_file_path, "w", encoding="utf-8") as f:
                f.write(clean_patch.strip())

            with open(test_file_path, "w", encoding="utf-8") as f:
                header = (
                    "import sys, os\n"
                    "sys.path.insert(0, os.path.dirname(__file__))\n"
                    "from solution import *\n\n"
                )
                f.write(header + clean_test.strip())

            try:
                # -p no:django mencegah pytest mencari konfigurasi Django
                result = subprocess.run(
                    ["pytest", test_file_path, "-v", "--tb=short", "-p", "no:django"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )

                is_passed = (result.returncode == 0)
                output = result.stdout if is_passed else (result.stdout + "\n" + result.stderr)

                return {
                    "passed": is_passed,
                    "output": output.strip()
                }
            except subprocess.TimeoutExpired:
                return {
                    "passed": False,
                    "output": f"Execution timed out after {timeout_seconds}s."
                }
            except Exception as e:
                return {
                    "passed": False,
                    "output": f"Sandbox execution error: {str(e)}"
                }