from sqlalchemy import Integer, String, Text, DateTime, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)  # "naukri", "linkedin"
    title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    skills: Mapped[dict] = mapped_column(JSON, nullable=True)  
    salary_min: Mapped[float] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float] = mapped_column(Float, nullable=True)
    experience_min: Mapped[float] = mapped_column(Float, nullable=True)
    job_url: Mapped[str] = mapped_column(String, nullable=False)
    posted_date: Mapped[str] = mapped_column(String, nullable=True)
    fetched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)