from sqlalchemy import Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="applied", nullable=False)  # applied, viewed, interview, rejected, offer
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    applied_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", backref="applications")
    job = relationship("Job")

    __table_args__ = (
        # One application per user per job
        __import__("sqlalchemy").UniqueConstraint("user_id", "job_id", name="uq_user_job"),
    )