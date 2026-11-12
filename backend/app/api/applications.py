from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_current_user
from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.user import User

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    job_id: int
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: str
    notes: Optional[str]
    applied_at: str
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    job_url: Optional[str] = None

    model_config = {"from_attributes": True}


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == payload.job_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already applied to this job")

    app = Application(
        user_id=current_user.id,
        job_id=payload.job_id,
        status="applied",
        notes=payload.notes,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    return _to_out(app, job)


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    apps = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.applied_at.desc()).all()

    results = []
    for app in apps:
        job = db.get(Job, app.job_id)
        results.append(_to_out(app, job))
    return results


@router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(
    app_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.get(Application, app_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.status is not None:
        allowed = {"applied", "viewed", "interview", "rejected", "offer"}
        if payload.status not in allowed:
            raise HTTPException(status_code=400, detail=f"Status must be one of {allowed}")
        app.status = payload.status
    if payload.notes is not None:
        app.notes = payload.notes

    db.commit()
    db.refresh(app)
    job = db.get(Job, app.job_id)
    return _to_out(app, job)


def _to_out(app: Application, job: Job | None) -> ApplicationOut:
    return ApplicationOut(
        id=app.id,
        job_id=app.job_id,
        status=app.status,
        notes=app.notes,
        applied_at=app.applied_at.isoformat(),
        job_title=job.title if job else None,
        job_company=job.company if job else None,
        job_url=job.job_url if job else None,
    )