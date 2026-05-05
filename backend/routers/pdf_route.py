from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_parser import parse_pdf

router = APIRouter(prefix="/api", tags=["pdf"])


@router.post("/parse-pdf")
async def parse_pdf_endpoint(pdf: UploadFile = File(...)):
    name = (pdf.filename or "").lower()
    if not name.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    data = await pdf.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty PDF file")

    try:
        result = parse_pdf(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {exc}")

    return result
