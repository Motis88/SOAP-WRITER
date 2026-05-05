from pydantic import BaseModel
from typing import List, Optional, Dict


class Vitals(BaseModel):
    temp: Optional[str] = None
    hr: Optional[str] = None
    rr: Optional[str] = None
    weight: Optional[str] = None
    bp: Optional[str] = None


class LabItem(BaseModel):
    name: str
    value: str
    unit: str = ""
    ref_range: str = ""
    flag: str = ""
    formatted: str = ""


class LabResults(BaseModel):
    cbc: List[LabItem] = []
    chemistry: List[LabItem] = []
    electrolytes: List[LabItem] = []
    snap: List[LabItem] = []
    urinalysis: List[LabItem] = []


class ObjectiveData(BaseModel):
    physical_exam: List[str] = []
    vitals: Vitals = Vitals()
    lab_results: LabResults = LabResults()


class SOAPRecord(BaseModel):
    subjective: List[str] = []
    objective: ObjectiveData = ObjectiveData()
    assessment: str = ""
    plan: str = ""
    flags: List[str] = []


class TextInput(BaseModel):
    text: str
