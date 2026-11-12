from sqlalchemy.orm import Session
from jobhunter import scrape_jobs

from app.models.job import Job


def fetch_naukri_jobs(db: Session, search_term: str, city: str | None = None, results_wanted: int = 20,) -> list[Job]:
    raw_jobs = scrape_jobs(
        search_term=search_term,
        sources=["naukri"],
        city=city,
        results_wanted=results_wanted,
    )

    inserted = []
    for raw in raw_jobs:
        import hashlib
        ext_id = f"naukri_{hashlib.md5(raw.job_url.encode()).hexdigest()[:12]}"

        existing = db.query(Job).filter(Job.external_id == ext_id).first()
        if existing:
            continue

        job = Job(
            external_id=ext_id,
            source="naukri",
            title=raw.title,
            company=raw.company,
            location=raw.location or "",
            description=raw.description or "",
            skills=raw.skills or [],
            salary_min=raw.salary.min_amount if raw.salary else None,
            salary_max=raw.salary.max_amount if raw.salary else None,
            experience_min=raw.experience_min,
            job_url=raw.job_url,
            posted_date=raw.date_posted,
        )
        db.add(job)
        inserted.append(job)

    db.commit()
    for job in inserted:
        db.refresh(job)

    return inserted