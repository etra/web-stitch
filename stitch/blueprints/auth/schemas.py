from pydantic import BaseModel, EmailStr


class AuthRequest(BaseModel):
    """Contract for email-only authentication (register or login)"""
    email: EmailStr


class UserResponse(BaseModel):
    """Contract for user response"""
    id: str
    email: str
    created_at: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Contract for authentication response"""
    user: UserResponse
    message: str
