from fastapi import APIRouter, HTTPException
from models.soap_models import TextInput
from services.soap_structurer import structure_text_to_soap

router = APIRouter(prefix="/api", tags=["soap"])


@router.post("/structure")
async def structure_endpoint(body: TextInput):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    result = structure_text_to_soap(body.text)
    return result
