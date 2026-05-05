"""
SOAP Structuring Service.

Takes raw transcribed / free text and structures it into S (Subjective) and
O (Objective) sections.  A and P are always left empty.

STRICT RULES:
  - No medical inference, diagnosis, differentials, or recommendations.
  - Only information present in the input is used.
  - If information is missing  → "לא נמסר"
  - If text is unclear         → "[לא ברור]"
"""

from __future__ import annotations

import re
from typing import List, Tuple

from app.models import SOAPNote, Objective, Vitals, LabResults


# ---------------------------------------------------------------------------
# Keyword sets (Hebrew + English) for routing sentences to S or O
# ---------------------------------------------------------------------------

_SUBJECTIVE_KEYWORDS_HE = [
    "בעל", "בעלים", "מדווח", "מדווחת", "תלונ", "היסטוריה", "הקא", "שלשול",
    "אוכל", "שותה", "שתיה", "אכיל", "פעיל", "עייפ", "עייפות", "צולע",
    "שיעול", "גרד", "גרדן", "נשר", "שיער", "כחכוח", "ירידה במשקל",
    "ירידה בתיאבון", "לא אוכל", "לא שותה", "הופי", "חולש", "ליחה",
    "פרכוס", "עוויתות", "קשי נשימה", "כאב", "צעקה", "בכי", "ירד",
    "עלה", "החמיר", "השתפר", "ימים", "שבועות", "חודשים", "שעות",
    "מאז", "לפני", "החל", "מתחיל",
]

_SUBJECTIVE_KEYWORDS_EN = [
    "owner", "report", "complaint", "history", "vomit", "diarrhea",
    "eating", "drinking", "active", "lethargic", "cough", "itch",
    "hair loss", "weight loss", "appetite", "not eating", "not drinking",
    "seizure", "dyspnea", "pain", "crying", "worsened", "improved",
    "days", "weeks", "months", "hours", "ago", "since", "started",
]

_OBJECTIVE_KEYWORDS_HE = [
    "בדיקה", "בדיקת", "חום", "טמפרטורה", "דופק", "נשימה", "משקל",
    "ריאות", "לב", "בטן", "עיניים", "אוזניים", "עור", "ריריות",
    "לחצי דם", "צבע", "טורגור", "כאב בבטן", "קול לב", "קול ריאות",
    "ממצא", "ממצאים", "מדד", "בדיקות דם", "תוצאות",
]

_OBJECTIVE_KEYWORDS_EN = [
    "exam", "physical", "temp", "temperature", "hr", "heart rate", "rr",
    "respiratory", "weight", "lung", "heart", "abdomen", "eye", "ear",
    "skin", "mucous", "blood pressure", "finding", "result", "lab",
    "measured", "auscultation", "palpation",
]

# Vital sign patterns (Hebrew + English)
_VITAL_PATTERNS = {
    "temp": [
        r"(?:חום|טמפרטורה|temp(?:erature)?)\s*[:=]?\s*(\d{2,3}(?:[.,]\d{1,2})?)",
    ],
    "hr": [
        r"(?:דופק|HR|heart\s*rate|pulse)\s*[:=]?\s*(\d{2,3})",
    ],
    "rr": [
        r"(?:נשימה|RR|respiratory\s*rate)\s*[:=]?\s*(\d{1,3})",
    ],
    "weight": [
        r"(?:משקל|weight)\s*[:=]?\s*(\d+(?:[.,]\d{1,2})?)\s*(?:ק[\"״]?ג|kg)?",
    ],
}


def _normalise(text: str) -> str:
    """Minimal normalisation — no meaning changes."""
    # Normalise line endings and remove duplicate spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _extract_vitals(text: str) -> Vitals:
    vitals: dict = {}
    for field, patterns in _VITAL_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                vitals[field] = m.group(1).replace(",", ".")
                break
    return Vitals(**vitals)


def _word_match(keyword: str, text: str) -> bool:
    """
    Check whether `keyword` appears as a whole word (or phrase) in `text`.
    Uses a simple whitespace-aware check compatible with Hebrew Unicode.
    """
    # Surround keyword with word-like boundaries: start/end of string or whitespace/punctuation
    pattern = r"(?:^|[\s,،.;:!?\"'()\[\]])" + re.escape(keyword) + r"(?:$|[\s,،.;:!?\"'()\[\]])"
    return bool(re.search(pattern, text))


def _score_sentence(sentence: str) -> Tuple[int, int]:
    """
    Returns (subj_score, obj_score) based on keyword hits.
    Higher score wins the category.
    Uses whole-word matching to avoid substring false positives
    (e.g. 'לב' matching inside 'כלב').
    """
    lower = sentence.lower()
    s_score = sum(1 for kw in _SUBJECTIVE_KEYWORDS_HE if _word_match(kw, sentence)) + \
               sum(1 for kw in _SUBJECTIVE_KEYWORDS_EN if _word_match(kw, lower))
    o_score = sum(1 for kw in _OBJECTIVE_KEYWORDS_HE if _word_match(kw, sentence)) + \
               sum(1 for kw in _OBJECTIVE_KEYWORDS_EN if _word_match(kw, lower))
    return s_score, o_score


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences on common separators, but not on decimal points."""
    # Replace decimal-point numbers temporarily to protect them
    text = re.sub(r"(\d)\.(\d)", r"\1DECPT\2", text)
    sentences = re.split(r"[.،,\n;]+", text)
    # Restore decimal points
    return [s.strip().replace("DECPT", ".") for s in sentences if s.strip()]


def structure_text(raw_text: str) -> SOAPNote:
    """
    Structure raw text into a SOAPNote.

    Only S and O are populated.  A and P remain empty strings.
    No medical reasoning is performed.
    """
    flags: List[str] = []
    text = _normalise(raw_text)

    if not text:
        flags.append("missing_data")
        return SOAPNote(flags=flags)

    sentences = _split_sentences(text)
    subjective: List[str] = []
    physical_exam: List[str] = []

    vitals = _extract_vitals(text)

    for sentence in sentences:
        s_score, o_score = _score_sentence(sentence)

        # Check for unclear content — use bounded match to prevent ReDoS
        if re.search(r"\[[^\]]{0,200}\]|\?{2,}|xxx|unclear", sentence, re.IGNORECASE):
            flags.append("unclear_text")
            sentence = f"[לא ברור] {sentence}"

        if o_score > s_score:
            # Remove already-extracted vital lines to avoid duplication
            is_vital_line = any(
                re.search(pat, sentence, re.IGNORECASE)
                for patterns in _VITAL_PATTERNS.values()
                for pat in patterns
            )
            if not is_vital_line:
                physical_exam.append(sentence)
        elif s_score > 0:
            subjective.append(sentence)
        else:
            # Default unclassified sentence to Subjective (owner's words)
            subjective.append(sentence)

    if not subjective:
        flags.append("missing_data")

    return SOAPNote(
        subjective=subjective if subjective else ["לא נמסר"],
        objective=Objective(
            physical_exam=physical_exam if physical_exam else [],
            vitals=vitals,
            lab_results=LabResults(),
        ),
        assessment="",
        plan="",
        flags=list(set(flags)),
    )
