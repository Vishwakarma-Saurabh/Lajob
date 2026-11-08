import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import COOKIE_NAME, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (LoginRequest, MessageOut, RegisterRequest, UserOut, VerifyRequest,)
from app.workers.tasks import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _generate_code() -> str:
    return f"{secrets.randbelow(9000) + 1000}"


@router.post("/register", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    existing = db.query(User).filter(User.email == email).first()

    # Do not leak whether the email exists.
    if existing and existing.is_verified:
        return MessageOut(message="If the email is available, a verification code has been sent.")

    code = _generate_code()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_TTL_MINUTES)

    if existing and not existing.is_verified:
        # Re-registration attempt — refresh the code.
        existing.hashed_password = hash_password(payload.password)
        existing.full_name = payload.full_name
        existing.verification_code = code
        existing.verification_code_expires_at = expires
        user = existing
    else:
        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            is_verified=False,
            verification_code=code,
            verification_code_expires_at=expires,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    send_verification_email.delay(user.email, code)
    return MessageOut(message="If the email is available, a verification code has been sent.")


@router.post("/verify", response_model=MessageOut)
def verify(payload: VerifyRequest, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or code")
    if user.is_verified:
        return MessageOut(message="Email already verified")
    if not user.verification_code or user.verification_code != payload.code:
        raise HTTPException(status_code=400, detail="Invalid email or code")
    if not user.verification_code_expires_at or user.verification_code_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code expired")

    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    db.commit()
    return MessageOut(message="Email verified successfully")


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    token = create_access_token(user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return user


@router.post("/logout", response_model=MessageOut)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return MessageOut(message="Logged out")


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user