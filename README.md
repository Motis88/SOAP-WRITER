# 🩺 SOAP Writer — רשומה וטרינרית

מערכת תמלול ועיבוד טקסט רפואי להמרת קלט (קולי / טקסט / PDF) לרשומת SOAP וטרינרית מסודרת.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Python FastAPI |
| STT | OpenAI Whisper |
| PDF / OCR | pdfplumber + Tesseract |
| DB (optional) | PostgreSQL |

---

## Features

- 🎙️ **הקלטה קולית** — תמלול אוטומטי עברית / אנגלית / מעורב (Whisper)
- ✏️ **קלט טקסט** — הזנה ידנית וחלוקה אוטומטית ל-S / O
- 📄 **העלאת PDF** — פענוח בדיקות IDEXX (CBC, Chemistry, SNAP, UA) כולל OCR
- 📋 **עריכה inline** — כל שדה ניתן לעריכה ישירה
- 📊 **תצוגה טבלאית** — ערכי מעבדה עם טווח ייחוס ודגלים H/L
- 📑 **העתק הכל** — פורמט SOAP מלא ללוח

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

> API זמין ב-`http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

> אפליקציה זמינה ב-`http://localhost:5173`

---

## Project Structure

```
SOAP-WRITER/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── requirements.txt
│   ├── models/
│   │   └── soap_models.py       # Pydantic schemas
│   ├── services/
│   │   ├── whisper_service.py   # STT
│   │   ├── pdf_parser.py        # PDF + OCR
│   │   └── soap_structurer.py   # Text → SOAP
│   └── routers/
│       ├── transcribe.py        # POST /api/transcribe
│       ├── pdf_route.py         # POST /api/parse-pdf
│       └── soap.py              # POST /api/structure
└── frontend/
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── RecordButton.jsx
        │   ├── PDFUpload.jsx
        │   ├── SOAPEditor.jsx
        │   └── LabResultsTable.jsx
        └── services/
            └── api.js
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/transcribe` | Audio file → text (Whisper) |
| POST | `/api/parse-pdf` | PDF → lab results JSON |
| POST | `/api/structure` | Free text → SOAP JSON |
| GET | `/api/health` | Health check |

---

## SOAP Output Rules

- **S / O** — מולאים אוטומטית מהקלט
- **A / P** — נשארים ריקים לעריכת הרופא
- אין אבחנות / פרשנות / המלצות — תמרון בלבד
