from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.services.job_fetcher import fetch_naukri_jobs
from app.services.matcher import match_resume_to_roles

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/fetch")
def trigger_fetch(
    search_term: str = Query(..., min_length=2),
    city: str | None = Query(None),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = fetch_naukri_jobs(db, search_term, city, limit)
    return {"fetched": len(jobs), "jobs": [{"id": j.id, "title": j.title, "company": j.company} for j in jobs]}


@router.get("/matches")
def get_job_matches(
    resume_id: int = Query(...),
    top_k: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    resume = db.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_skills = set(resume.parsed_data.get("skills", []) if resume.parsed_data else [])
    if not resume_skills:
        raise HTTPException(status_code=400, detail="No skills found in resume")

    all_jobs = db.query(Job).order_by(Job.fetched_at.desc()).limit(200).all()

    scored = []
    for job in all_jobs:
        job_skills = set(job.skills or [])
        if not job_skills:
            continue
        overlap = resume_skills & job_skills
        score = len(overlap) / len(resume_skills) if resume_skills else 0
        if score > 0:
            scored.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url,
                "score": round(score, 3),
                "matched_skills": sorted(overlap),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"resume_id": resume_id, "matches": scored[:top_k]}