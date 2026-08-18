import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .schemas import CodeAnalysisResult

class CodeAnalysisAgent:
    def __init__(self):
        api_key = os.getenv("AQ.Ab8RN6K74WneIbfoKx5dRmMjztIf_9R_7c9YkRvQT8jbCZA7Uw")
        # Menggunakan model gemini-2.5-flash (atau gemini-1.5-flash-latest)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=api_key,
            temperature=0.1
        )
        self.structured_llm = self.llm.with_structured_output(CodeAnalysisResult)

    def analyze(self, code_diff: str) -> CodeAnalysisResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert Senior Security Engineer and Automated Code Reviewer. "
                "Analyze the provided Git code diff carefully. "
                "Detect security vulnerabilities, potential performance bottlenecks, and logical bugs. "
                "Provide actionable patches and comprehensive unit tests to prevent regressions."
            )),
            ("human", "Here is the code diff to analyze:\n\n```\n{diff}\n```")
        ])

        chain = prompt | self.structured_llm
        return chain.invoke({"diff": code_diff})