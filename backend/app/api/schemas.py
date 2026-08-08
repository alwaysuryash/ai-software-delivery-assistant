"""API DTOs (request/response models). Kept separate from domain + ORM models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.domain.enums import Health, Role


class DevLoginRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: Role


class ProjectSummary(BaseModel):
    id: str
    name: str
    owner: str
    status: str
    current_health: Health = Health.UNKNOWN


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    time: datetime
