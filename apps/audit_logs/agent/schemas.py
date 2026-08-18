from pydantic import BaseModel, Field
from typing import List

class VulnerabilityItem(BaseModel):
    title: str = Field(description="Nama kerentanan atau bug, misal: SQL Injection, Missing Auth")
    severity: str = Field(description="Tingkat keparahan: LOW, MEDIUM, HIGH, CRITICAL")
    description: str = Field(description="Penjelasan ringkas letak celah keamanan dan dampaknya")
    line_number: str = Field(description="Perkiraan baris kode atau fungsi terkait")

class CodeAnalysisResult(BaseModel):
    vulnerabilities: List[VulnerabilityItem] = Field(default_factory=list, description="Daftar bug atau celah yang ditemukan")
    patch: str = Field(description="Kode perbaikan lengkap dalam format diff atau block code")
    unit_test: str = Field(description="Unit test Python/Pytest untuk memverifikasi bug tersebut sudah teratasi")