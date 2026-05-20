from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Medicopter API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "production"] = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./medselo.db"

    # JWT
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24       # 1 день
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Роли пользователей
    USER_ROLES: list[str] = ["patient", "doctor", "dispatcher", "admin"]

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if v == "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32":
            import warnings
            warnings.warn("⚠️  Используется дефолтный SECRET_KEY! Смените в .env перед деплоем.")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
