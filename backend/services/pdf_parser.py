import re
import io
from typing import Dict, List, Optional, Tuple

import pdfplumber

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# -------------------------------------------------------------------
# Analyte classification lists
# -------------------------------------------------------------------
CBC_ANALYTES = {
    "WBC", "RBC", "HGB", "HCT", "MCV", "MCH", "MCHC", "RDW",
    "PLT", "MPV", "NEU", "LYM", "MONO", "EOS", "BASO",
    "NNEU", "NLYM", "NMONO", "NEOS", "NBASO",
}

CHEMISTRY_ANALYTES = {
    "ALT", "AST", "ALKP", "GGT", "TBIL", "TP", "ALB", "GLOB",
    "BUN", "CREA", "SDMA", "GLU", "CHOL", "AMYL", "LIPA",
    "PHOS", "CA", "CALCIUM", "A/G", "AG",
}

ELECTROLYTE_ANALYTES = {"NA", "K", "CL", "TCO2", "HCO3", "NA+", "K+", "CL-"}

UA_ANALYTES = {
    "USG", "PH", "PROTEIN", "GLUCOSE", "KETONES",
    "BILIRUBIN", "BLOOD", "NITRITE", "LEUKOCYTES",
    "COLOR", "APPEARANCE", "CAST", "BACTERIA",
}

# -------------------------------------------------------------------
# Lab line parsing
# -------------------------------------------------------------------
# Matches: Name  Value  Unit  Ref-Range  Flag?
_LINE_FULL = re.compile(
    r"^([A-Za-z][A-Za-z0-9/\s]{0,20}?)\s+"
    r"([<>]?\d+\.?\d*)\s+"
    r"([A-Za-z%/µuU][A-Za-z0-9/µuU.]*)\s+"
    r"(\d+\.?\d*\s*[-–]\s*\d+\.?\d*)\s*"
    r"([HLhl\*]?)$"
)
# Matches: Name  Value  Unit  Flag?  (no range)
_LINE_SHORT = re.compile(
    r"^([A-Za-z][A-Za-z0-9/\s]{0,20}?)\s+"
    r"([<>]?\d+\.?\d*)\s+"
    r"([A-Za-z%/µuU][A-Za-z0-9/µuU.]*)\s*"
    r"([HLhl\*]?)$"
)


def _make_item(name: str, value: str, unit: str, ref: str, flag: str) -> Dict:
    flag = flag.upper()
    parts = [f"{name}: {value} {unit}".strip()]
    if ref:
        parts[0] += f" ({ref})"
    if flag:
        parts[0] += f" [{flag}]"
    return {
        "name": name.upper(),
        "value": value,
        "unit": unit,
        "ref_range": ref,
        "flag": flag,
        "formatted": parts[0],
    }


def _parse_line(line: str) -> Optional[Dict]:
    line = line.strip()
    if not line or len(line) < 4:
        return None
    m = _LINE_FULL.match(line)
    if m:
        return _make_item(m.group(1).strip(), m.group(2), m.group(3), m.group(4), m.group(5) or "")
    m = _LINE_SHORT.match(line)
    if m:
        return _make_item(m.group(1).strip(), m.group(2), m.group(3), "", m.group(4) or "")
    return None


def _classify(name: str) -> str:
    n = name.upper().strip().rstrip("+-")
    if n in CBC_ANALYTES:
        return "cbc"
    if n in CHEMISTRY_ANALYTES:
        return "chemistry"
    if n in ELECTROLYTE_ANALYTES:
        return "electrolytes"
    if n in UA_ANALYTES:
        return "urinalysis"
    return "unknown"


# -------------------------------------------------------------------
# Report-type detection
# -------------------------------------------------------------------
def detect_report_types(text: str) -> List[str]:
    up = text.upper()
    types: List[str] = []
    if any(k in up for k in ("PROCYTE", "HEMATOLOGY", "CBC")):
        types.append("cbc")
    if any(k in up for k in ("CATALYST", "CHEMISTRY", "BIOCHEMISTRY")):
        types.append("chemistry")
    if "SNAP" in up:
        types.append("snap")
    if any(k in up for k in ("URINALYSIS", "URINE ANALYSIS", "UA STRIP")):
        types.append("urinalysis")
    return types or ["unknown"]


# -------------------------------------------------------------------
# Section parsers
# -------------------------------------------------------------------
def _parse_by_set(text: str, analyte_set: set) -> List[Dict]:
    results: List[Dict] = []
    seen: set = set()
    for line in text.splitlines():
        item = _parse_line(line)
        if item and item["name"] in analyte_set and item["name"] not in seen:
            results.append(item)
            seen.add(item["name"])
    return results


def _parse_snap(text: str) -> List[Dict]:
    results: List[Dict] = []
    pattern = re.compile(
        r"(4DX|SNAP\s+\w+|FELV/FIV|FELV|FIV|HEARTWORM|PARVO|CPL)"
        r"[:\s]+(POSITIVE|NEGATIVE|POS|NEG|REACTIVE|NON[-\s]?REACTIVE|\+|-)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        name = m.group(1).strip().upper()
        value = m.group(2).strip().upper()
        results.append(_make_item(name, value, "", "", ""))
    return results


def _parse_ua(text: str) -> List[Dict]:
    results: List[Dict] = []
    seen: set = set()
    for ua in UA_ANALYTES:
        m = re.search(rf"\b{ua}\b[:\s]+([^\n\r]+)", text, re.IGNORECASE)
        if m and ua not in seen:
            raw = m.group(1).strip().split()[0]
            results.append(_make_item(ua, raw, "", "", ""))
            seen.add(ua)
    return results


# -------------------------------------------------------------------
# PDF text extraction
# -------------------------------------------------------------------
def _extract_text(pdf_bytes: bytes) -> Tuple[str, List[str]]:
    flags: List[str] = []
    full = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if len(page_text.strip()) > 20:
                full += page_text + "\n"
            elif OCR_AVAILABLE:
                flags.append("ocr_used")
                try:
                    img = page.to_image(resolution=300).original
                    full += pytesseract.image_to_string(img, lang="eng") + "\n"
                except Exception:
                    flags.append("partial_extraction")
    return full, flags


# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------
def parse_pdf(pdf_bytes: bytes) -> Dict:
    flags: List[str] = []
    empty_labs = {
        "cbc": [], "chemistry": [], "electrolytes": [],
        "snap": [], "urinalysis": [],
    }

    try:
        text, ext_flags = _extract_text(pdf_bytes)
        flags.extend(ext_flags)

        if not text.strip():
            flags.append("partial_extraction")
            return {"lab_results": empty_labs, "raw_text": "", "flags": flags}

        report_types = detect_report_types(text)
        if "unknown" in report_types:
            flags.append("unknown_pdf_format")
            report_types = ["cbc", "chemistry", "snap", "urinalysis"]

        lab_results: Dict[str, List] = {
            "cbc": _parse_by_set(text, CBC_ANALYTES) if "cbc" in report_types else [],
            "chemistry": _parse_by_set(text, CHEMISTRY_ANALYTES) if "chemistry" in report_types else [],
            "electrolytes": _parse_by_set(text, ELECTROLYTE_ANALYTES) if "chemistry" in report_types else [],
            "snap": _parse_snap(text) if "snap" in report_types else [],
            "urinalysis": _parse_ua(text) if "urinalysis" in report_types else [],
        }

        return {
            "lab_results": lab_results,
            "raw_text": text,
            "flags": list(set(flags)),
        }

    except Exception as exc:
        return {
            "lab_results": empty_labs,
            "raw_text": "",
            "flags": ["partial_extraction"],
            "error": str(exc),
        }
