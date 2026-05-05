# 🐾 SOAP Writer — תמלול וטרינרי

אפליקציית תמלול ועיבוד טקסט רפואי וטרינרי.  
ממירה קלט (קול / טקסט / PDF) לרישום **SOAP** מסודר — **ללא פרשנות רפואית**.

---

## סקירה כללית

| שלב | תיאור |
|-----|-------|
| **STT** | תמלול קולי עברית/אנגלית/משולב — Whisper |
| **Structuring** | חלוקה ל-S/O בלבד על-פי תוכן בלבד |
| **PDF Parsing** | חילוץ ערכי בדיקות דם מדוחות IDEXX |
| **OCR** | זיהוי טקסט ב-PDF סרוקים — Tesseract |

**כלל בסיסי:** A ו-P נשארים ריקים תמיד.  
אין פרשנות, אין הסקת מסקנות, אין המלצות.

---

## מבנה הפרויקט

```
SOAP-WRITER/
├── backend/              # FastAPI + Python
│   ├── app/
│   │   ├── main.py           # FastAPI app entry-point
│   │   ├── models.py         # Pydantic data models
│   │   ├── api/
│   │   │   └── endpoints.py  # API routes
│   │   └── services/
│   │       ├── stt_service.py   # Whisper STT
│   │       ├── soap_service.py  # Text → SOAP structuring
│   │       └── pdf_service.py   # IDEXX PDF parsing
│   ├── tests/                # pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── RecordButton.jsx   # 🎙 Audio recording
│   │   │   ├── PDFUpload.jsx      # 📄 Drag & drop PDF
│   │   │   ├── SOAPDisplay.jsx    # SOAP note renderer
│   │   │   └── LabTable.jsx       # Lab results table
│   │   ├── hooks/
│   │   │   └── useRecorder.js     # MediaRecorder hook
│   │   └── services/
│   │       └── api.js             # API client
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/transcribe` | Audio → text (Whisper) |
| `POST` | `/api/structure` | Text → SOAP note |
| `POST` | `/api/parse-pdf` | IDEXX PDF → lab results |
| `POST` | `/api/process` | Full pipeline (audio + text + PDF) |
| `GET`  | `/health` | Health check |

### POST `/api/structure`
```json
{ "text": "כלב בן 5, הקאות יומיים, בבדיקה חום 39.5" }
```

Response:
```json
{
  "subjective": ["כלב בן 5", "הקאות יומיים"],
  "objective": {
    "physical_exam": [],
    "vitals": { "temp": "39.5", "hr": null, "rr": null, "weight": null },
    "lab_results": { "cbc": [], "chemistry": [], "electrolytes": [], "snap": [], "urinalysis": [] }
  },
  "assessment": "",
  "plan": "",
  "flags": []
}
```

---

## PDF Reports Supported (IDEXX)

| Report | Panel | Tests |
|--------|-------|-------|
| ProCyte | CBC | WBC, RBC, HGB, HCT, MCV, MCH, MCHC, RDW, PLT, MPV |
| Catalyst | Chemistry | ALT, AST, ALKP, GGT, TBIL, TP, ALB, GLOB, BUN, CREA, SDMA, GLU, CHOL, AMYL, LIPA, PHOS, Ca |
| Catalyst | Electrolytes | Na, K, Cl, tCO2 |
| SNAP | SNAP | Positive / Negative results |
| UA | Urinalysis | USG, pH, Protein, Glucose, Ketones, Bilirubin, Blood |

---

## הרצה מהירה (Docker)

```bash
docker-compose up --build
```

- Frontend: http://localhost:5173  
- Backend API: http://localhost:8000/docs

---

## הרצה מקומית

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Tests
```bash
cd backend
python -m pytest tests/ -v
```

---

## תכונות ממשק

- 🎙 **הקלטה** — כפתור הקלטה עם תמלול חי ב-Whisper
- 📄 **העלאת PDF** — Drag & Drop לדוחות IDEXX
- ✏️ **עריכה inline** — לחיצה על כל שדה לעריכה
- 📋 **העתק הכל** — ייצוא SOAP לטקסט
- ⚠️ **סימון שדות לא ברורים** — הדגשה בצהוב
- 🧪 **תצוגה טבלאית** — בדיקות דם בטבלה עם דגלי H/L

---

## Flags

| Flag | משמעות |
|------|--------|
| `missing_data` | חסר מידע |
| `unclear_text` | טקסט לא ברור |
| `ocr_used` | שימוש ב-OCR |
| `partial_extraction` | חילוץ חלקי |
| `unknown_pdf_format` | פורמט PDF לא מוכר |
