from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, resumes, jobs, applications
from app.config import settings

app = FastAPI(title="Resume SaaS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(applications.router)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}