import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .schemas import CodeAnalysisResult

class CodeAnalysisAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=api_key
        )
        self.structured_llm = self.llm.with_structured_output(CodeAnalysisResult)

    def analyze(self, code_diff: str) -> CodeAnalysisResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert Senior Security Engineer and Automated Code Reviewer. "
                "Analyze the provided Git code diff carefully. "
                "Detect security vulnerabilities, potential performance bottlenecks, and logical bugs. "
                "Provide actionable patches as clean executable Python code and comprehensive pytest unit tests."
            )),
            ("human", "Here is the code diff to analyze:\n\n```\n{diff}\n```")
        ])

        chain = prompt | self.structured_llm
        return chain.invoke({"diff": code_diff})

    def fix_patch_and_test(self, original_diff: str, current_patch: str, current_test: str, error_log: str) -> CodeAnalysisResult:
        """
        Feedback loop untuk memperbaiki patch atau unit test saat pengujian sandbox gagal.
        """
        correction_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert Automated Debugger. A previous patch or unit test failed during execution in the pytest sandbox runner. "
                "Analyze the failure output carefully, fix the Python implementation and pytest test suite, and ensure all tests will pass cleanly."
            )),
            ("human", (
                "Original Diff:\n```\n{diff}\n```\n\n"
                "Current Patch:\n```\n{patch}\n```\n\n"
                "Current Unit Test:\n```\n{test}\n```\n\n"
                "Test Runner Failure Output:\n```\n{error}\n```\n\n"
                "Please generate the corrected patch and unit test."
            ))
        ])

        chain = correction_prompt | self.structured_llm
        return chain.invoke({
            "diff": original_diff,
            "patch": current_patch,
            "test": current_test,
            "error": error_log
        })