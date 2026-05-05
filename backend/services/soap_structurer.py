import re
from typing import List, Dict, Optional, Tuple

# Keywords indicating subjective (owner-reported) content
S_KEYWORDS = [
    # Hebrew
    "תלונ", "הקא", "שלשול", "אכיל", "תיאבון", "חולה", "עייפ", "עצלנ",
    "גרד", "שיעול", "דם ב", "צמא", "צלע", "נפיח", "כאב",
    "בעלים", "בעל", "בעליו", "בעלת", "הגיע", "מגיע",
    "ימים", "שבועות", "חודשים", "מאתמול", "מאז",
    "היסטוריה", "רקע", "חיסון", "תרופ", "טיפול קוד",
    "כלב בן", "חתול בן", "גיל", "מין", "אינו", "לא אוכל", "ירידה",
    "שתן מרוב", "הקאה", "שלשול",
    # English
    "owner", "complaint", "history", "vomit", "diarrhea", "not eating",
    "anorexia", "letharg", "weakness", "cough", "scratch", "polyuria",
    "polydipsia", "limp", "swelling", "pain", "since", "days ago",
    "week", "month", "previous", "reported", "presented", "has been",
]

# Keywords indicating objective (clinician-observed) content
O_KEYWORDS = [
    # Hebrew
    "בדיקה גופנ", "ממשש", "השמע", "ריאות", "לב", "בטן", "לימפה",
    "עינים", "אוזניים", "עור", "ריריות", "זמן מילוי",
    "טמפ", "חום", "דופק", "נשימות", "משקל", "לחץ דם",
    "ממצא", "פרפוזיה", "הידרציה", "גוון", "תגובה",
    # English
    "physical exam", "auscultation", "palpation", "mucous membrane", "CRT",
    "temperature", "heart rate", "respiratory rate", "weight", "blood pressure",
    "lymph", "abdomen", "thorax", "lung", "heart", "skin",
    "hydration", "perfusion",
]

# Vital extraction regex patterns
VITAL_PATTERNS: Dict[str, List[str]] = {
    "temp": [
        r"(?:temp(?:erature)?|חום|טמפ(?:רטורה)?)[:\s=]*(\d{2,3}\.?\d*)\s*(?:°[CF]|°|celsius)?",
        r"(\d{2,3}\.?\d*)\s*°[CF]",
    ],
    "hr": [
        r"(?:hr|pulse|heart\s*rate|דופק|פולס)[:\s=]*(\d{2,3})\s*(?:bpm|/min|לדקה)?",
        r"(\d{2,3})\s*bpm",
    ],
    "rr": [
        r"(?:rr|respiratory\s*rate|resp|נשימות|קצב\s*נשימה)[:\s=]*(\d{1,3})\s*(?:/min|לדקה)?",
    ],
    "weight": [
        r"(?:weight|wt|משקל)[:\s=]*(\d+\.?\d*)\s*(?:kg|ק[\"ג]|קג)?",
    ],
    "bp": [
        r"(?:bp|blood\s*pressure|לחץ\s*דם)[:\s=]*(\d{2,3}[/\\]\d{2,3})\s*(?:mmhg)?",
    ],
}


def extract_vitals(text: str) -> Dict[str, Optional[str]]:
    vitals: Dict[str, Optional[str]] = {
        "temp": None, "hr": None, "rr": None, "weight": None, "bp": None
    }
    text_lower = text.lower()
    for vital, patterns in VITAL_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                vitals[vital] = match.group(1)
                break
    return vitals


def score_sentence(sentence: str) -> Tuple[float, float]:
    low = sentence.lower()
    s_score = sum(1 for kw in S_KEYWORDS if kw.lower() in low)
    o_score = sum(1 for kw in O_KEYWORDS if kw.lower() in low)
    # Numbers with clinical units lean objective
    if re.search(r'\d+\.?\d*\s*(?:°|kg|bpm|/min|mmhg|%)', low):
        o_score += 1
    return float(s_score), float(o_score)


def split_into_sentences(text: str) -> List[str]:
    parts = re.split(r'[.!?;\n]+', text)
    result: List[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) > 100:
            sub = re.split(r',\s*', part)
            result.extend(p.strip() for p in sub if p.strip())
        else:
            result.append(part)
    return [s for s in result if len(s) > 2]


def structure_text_to_soap(text: str) -> Dict:
    flags: List[str] = []
    subjective: List[str] = []
    physical_exam: List[str] = []

    if not text or not text.strip():
        flags.append("missing_data")
        return _build_response(subjective, physical_exam, {}, flags)

    if "[לא ברור]" in text or "[unclear]" in text.lower():
        flags.append("unclear_text")

    vitals = extract_vitals(text)

    sentences = split_into_sentences(text)
    for sentence in sentences:
        s_score, o_score = score_sentence(sentence)
        if o_score > s_score:
            physical_exam.append(sentence)
        elif s_score > 0:
            subjective.append(sentence)
        else:
            subjective.append(sentence)

    if not subjective:
        flags.append("missing_data")

    return _build_response(subjective, physical_exam, vitals, flags)


def _build_response(
    subjective: List[str],
    physical_exam: List[str],
    vitals: Dict,
    flags: List[str],
) -> Dict:
    vitals_out = {
        "temp": vitals.get("temp") or "לא נמסר",
        "hr": vitals.get("hr") or "לא נמסר",
        "rr": vitals.get("rr") or "לא נמסר",
        "weight": vitals.get("weight") or "לא נמסר",
        "bp": vitals.get("bp") or "לא נמסר",
    }
    return {
        "subjective": subjective if subjective else ["לא נמסר"],
        "objective": {
            "physical_exam": physical_exam if physical_exam else ["לא נמסר"],
            "vitals": vitals_out,
            "lab_results": {
                "cbc": [],
                "chemistry": [],
                "electrolytes": [],
                "snap": [],
                "urinalysis": [],
            },
        },
        "assessment": "",
        "plan": "",
        "flags": list(set(flags)),
    }
