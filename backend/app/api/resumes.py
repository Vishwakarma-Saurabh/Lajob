import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.resume import Resume
from app.models.user import User
from app.services.matcher import match_resume_to_roles
from app.services.parser import parse_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_and_parse(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
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

    parsed = parse_resume(path)

    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_path=path,
        parsed_data=parsed,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "resume_id": resume.id,
        "filename": file.filename,
        "skills": parsed["skills"],
        "education": parsed["education"],
        "experience_years": parsed["experience_years"],
        "error": parsed["error"],
    }


@router.get("/{resume_id}/matches")
def get_matches(
    resume_id: int,
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = db.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_data or resume.parsed_data.get("error"):
        raise HTTPException(status_code=400, detail="Resume could not be parsed")

    skills = resume.parsed_data.get("skills", [])
    matches = match_resume_to_roles(skills, top_k=top_k)
    return {"resume_id": resume_id, "matches": matches}