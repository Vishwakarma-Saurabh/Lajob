from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=4)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    is_verified: bool

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    message: str