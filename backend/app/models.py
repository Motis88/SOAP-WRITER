"""
Pydantic models for the Veterinary SOAP Writer application.
All fields are strictly transcription/extraction only — no medical reasoning.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class LabResult(BaseModel):
    test: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None


class Vitals(BaseModel):
    temp: Optional[str] = None
    hr: Optional[str] = None
    rr: Optional[str] = None
    weight: Optional[str] = None


class LabResults(BaseModel):
    cbc: List[LabResult] = []
    chemistry: List[LabResult] = []
    electrolytes: List[LabResult] = []
    snap: List[LabResult] = []
    urinalysis: List[LabResult] = []


class Objective(BaseModel):
    physical_exam: List[str] = []
    vitals: Vitals = Vitals()
    lab_results: LabResults = LabResults()


class SOAPNote(BaseModel):
    subjective: List[str] = []
    objective: Objective = Objective()
    assessment: str = ""
    plan: str = ""
    flags: List[str] = []


class TranscribeResponse(BaseModel):
    text: str
    language: Optional[str] = None


class StructureRequest(BaseModel):
    text: str


class PDFParseResponse(BaseModel):
    report_type: str
    lab_results: LabResults = LabResults()
    flags: List[str] = []
