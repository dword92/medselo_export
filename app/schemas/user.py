from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
import re

from app.models.user import UserRole


# ── Вспомогательные ──────────────────────────────────────────────────────────

def _normalize_phone(phone: str) -> str:
    """
    Нормализуем к формату +7XXXXXXXXXX.
    Принимает любой формат: +7 700 123 45 67 / 87001234567 / 77001234567 / 7001234567
    """
    digits = re.sub(r"\D", "", phone)
    # +77001234567 → 12 цифр начиная с 77
    if len(digits) == 12 and digits.startswith("77"):
        return "+" + digits
    # 77001234567 или 87001234567 → 11 цифр
    if len(digits) == 11 and digits.startswith(("7", "8")):
        return "+7" + digits[1:]
    # 7001234567 → 10 цифр
    if len(digits) == 10:
        return "+7" + digits
    raise ValueError(
        f"Неверный номер. Введите в формате +7XXXXXXXXXX (цифр введено: {len(digits)})"
    )


# ── Регистрация ───────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    phone: str = Field(..., examples=["+77001234567"])
    full_name: str = Field(..., min_length=2, max_length=255, examples=["Айгуль Сатова"])
    password: str = Field(..., min_length=6, max_length=128)
    region: str | None = Field(None, max_length=255, examples=["Алматинская область"])
    village: str | None = Field(None, max_length=255, examples=["Каскелен"])

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _normalize_phone(v)

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Имя не может быть пустым")
        return v.strip()


# ── Вход ─────────────────────────────────────────────────────────────────────

class UserLogin(BaseModel):
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _normalize_phone(v)


# ── Ответы ───────────────────────────────────────────────────────────────────

class UserPublic(BaseModel):
    id: int
    phone: str
    full_name: str
    role: UserRole
    region: str | None
    village: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    region: str | None = Field(None, max_length=255)
    village: str | None = Field(None, max_length=255)
    email: str | None = None


# ── Токены ───────────────────────────────────────────────────────────────────

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
