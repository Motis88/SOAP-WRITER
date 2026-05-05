"""
PDF Parsing Service — IDEXX report extraction.

Supported report types:
  - ProCyte  → CBC
  - Catalyst → Chemistry + Electrolytes
  - SNAP     → SNAP tests
  - UA       → Urinalysis

STRICT RULES:
  - Values extracted verbatim from the PDF.
  - No medical interpretation or inference.
  - Unclear values → "[unclear value]"
  - OCR used when PDF contains scanned images.
"""

from __future__ import annotations

import io
import re
from typing import List, Optional, Tuple

from app.models import LabResult, LabResults, PDFParseResponse


# ---------------------------------------------------------------------------
# Panel definitions — tests to look for per report type
# ---------------------------------------------------------------------------

CBC_TESTS = ["WBC", "RBC", "HGB", "HCT", "MCV", "MCH", "MCHC", "RDW", "PLT", "MPV"]

CHEMISTRY_TESTS = [
    "ALT", "AST", "ALKP", "GGT", "TBIL", "TP", "ALB", "GLOB", "A/G",
    "BUN", "CREA", "SDMA", "GLU", "CHOL", "AMYL", "LIPA", "PHOS", "Ca",
]

ELECTROLYTE_TESTS = ["Na", "K", "Cl", "tCO2", "HCO3"]

URINALYSIS_TESTS = ["USG", "pH", "Protein", "Glucose", "Ketones", "Bilirubin", "Blood"]

# Detection keywords per report type
_TYPE_KEYWORDS = {
    "procyte": ["procyte", "cbc", "complete blood count"],
    "catalyst": ["catalyst", "chemistry", "biochem"],
    "snap": ["snap", "snap test", "snap 4dx", "snap fiv", "snap felv"],
    "ua": ["urinalysis", "urine", "ua", "u/a"],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NUMBER_RE = r"(\d[\d,\.]*)"
_FLAG_RE = r"\b(H|L|HH|LL|\*|HIGH|LOW|CRITICAL)\b"
_RANGE_RE = r"(\d[\d,\.]*\s*[-–]\s*\d[\d,\.]*)"
_UNIT_RE = r"([a-zA-Z/%µ·]+(?:/[a-zA-Z³]+)?)"


def _extract_pdf_text(pdf_bytes: bytes) -> Tuple[str, bool]:
    """
    Extract text from PDF.  Falls back to OCR for scanned PDFs.
    Returns (text, ocr_used).
    """
    ocr_used = False
    try:
        import pdfplumber
    except ImportError:
        return "[pdfplumber not installed]", False

    text_parts: List[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()

    # If text is sparse (scanned PDF), attempt OCR
    if len(full_text) < 50:
        ocr_used = True
        try:
            import pytesseract
            from PIL import Image

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                ocr_parts: List[str] = []
                for page in pdf.pages:
                    img = page.to_image(resolution=300).original
                    ocr_parts.append(pytesseract.image_to_string(img, lang="eng"))
            full_text = "\n".join(ocr_parts).strip()
        except Exception:
            pass  # Return whatever text we have

    return full_text, ocr_used


def _detect_report_type(text: str) -> str:
    lower = text.lower()
    for report_type, keywords in _TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return report_type
    return "unknown"


def _parse_test_line(line: str, test_name: str) -> Optional[LabResult]:
    """
    Parse a single line that is expected to contain a test result.

    Tries to extract: value, unit, reference range, flag.
    Pattern: TEST_NAME  VALUE  UNIT  RANGE  FLAG
    """
    # Remove the test name from the beginning of the line for cleaner parsing
    pattern = re.compile(
        r"(?i)" + re.escape(test_name) + r"[\s:]*" +
        r"(?P<value>" + _NUMBER_RE + r")" +
        r"[\s]*(?P<unit>" + _UNIT_RE + r")?" +
        r"[\s]*(?P<range>" + _RANGE_RE + r")?" +
        r"[\s]*(?P<flag>" + _FLAG_RE + r")?",
        re.IGNORECASE,
    )
    m = pattern.search(line)
    if m:
        value = m.group("value") or "[unclear value]"
        unit = m.group("unit")
        ref_range = m.group("range")
        flag = m.group("flag")
        return LabResult(
            test=test_name,
            value=value,
            unit=unit,
            reference_range=ref_range,
            flag=flag,
        )

    # Fallback: look for any number on the line
    nums = re.findall(r"\d[\d,.]*", line)
    if nums:
        return LabResult(test=test_name, value=nums[0])

    return None


def _extract_tests(text: str, test_names: List[str]) -> List[LabResult]:
    """Search the full PDF text for each test and extract its row."""
    results: List[LabResult] = []
    lines = text.splitlines()
    for test in test_names:
        pattern = re.compile(r"\b" + re.escape(test) + r"\b", re.IGNORECASE)
        for line in lines:
            if pattern.search(line):
                result = _parse_test_line(line, test)
                if result:
                    results.append(result)
                    break  # one result per test
    return results


def _extract_snap(text: str) -> List[LabResult]:
    """
    Extract SNAP test results.
    Each SNAP result is a test name + Positive/Negative/Reactive.
    """
    results: List[LabResult] = []
    for line in text.splitlines():
        m = re.search(
            r"([A-Za-z0-9 /\-]+?)\s*[:–-]\s*(Positive|Negative|Reactive|Non-Reactive|pos|neg)",
            line,
            re.IGNORECASE,
        )
        if m:
            results.append(LabResult(test=m.group(1).strip(), value=m.group(2).strip()))
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pdf(pdf_bytes: bytes) -> PDFParseResponse:
    """
    Parse an IDEXX PDF report and return structured lab results.

    No medical interpretation is performed.
    Values are extracted verbatim.
    """
    flags: List[str] = []
    text, ocr_used = _extract_pdf_text(pdf_bytes)

    if ocr_used:
        flags.append("ocr_used")

    if not text or len(text.strip()) < 10:
        flags.append("partial_extraction")
        return PDFParseResponse(
            report_type="unknown",
            lab_results=LabResults(),
            flags=flags,
        )

    report_type = _detect_report_type(text)

    if report_type == "unknown":
        flags.append("unknown_pdf_format")

    lab_results = LabResults()

    if report_type == "procyte":
        lab_results.cbc = _extract_tests(text, CBC_TESTS)

    elif report_type == "catalyst":
        lab_results.chemistry = _extract_tests(text, CHEMISTRY_TESTS)
        lab_results.electrolytes = _extract_tests(text, ELECTROLYTE_TESTS)

    elif report_type == "snap":
        lab_results.snap = _extract_snap(text)

    elif report_type == "ua":
        lab_results.urinalysis = _extract_tests(text, URINALYSIS_TESTS)

    else:
        # Unknown — attempt to extract all known panels
        flags.append("partial_extraction")
        lab_results.cbc = _extract_tests(text, CBC_TESTS)
        lab_results.chemistry = _extract_tests(text, CHEMISTRY_TESTS)
        lab_results.electrolytes = _extract_tests(text, ELECTROLYTE_TESTS)
        lab_results.snap = _extract_snap(text)
        lab_results.urinalysis = _extract_tests(text, URINALYSIS_TESTS)

    # Check if anything was actually found
    total = (
        len(lab_results.cbc)
        + len(lab_results.chemistry)
        + len(lab_results.electrolytes)
        + len(lab_results.snap)
        + len(lab_results.urinalysis)
    )
    if total == 0:
        flags.append("partial_extraction")

    return PDFParseResponse(
        report_type=report_type,
        lab_results=lab_results,
        flags=list(set(flags)),
    )
