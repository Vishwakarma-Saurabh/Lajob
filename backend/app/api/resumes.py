import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import settings
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/resumes", tags=["resumes"])

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    safe_name = f"{current_user.id}_{uuid.uuid4().hex}.pdf"
    path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(contents)

    return {
        "filename": file.filename,
        "stored_as": safe_name,
        "size_bytes": len(contents),
        "status": "uploaded",
    }