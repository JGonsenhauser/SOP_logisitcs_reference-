"""
SOP App - Pydantic response models.
"""
from pydantic import BaseModel
from typing import Optional, Any


class LoginResponse(BaseModel):
    token: str
    user: dict


class ErrorResponse(BaseModel):
    error: str


class MessageResponse(BaseModel):
    message: str
    id: Optional[int] = None
