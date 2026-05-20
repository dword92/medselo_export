from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenPair


class UserService:

    # ── Регистрация ───────────────────────────────────────────────────────────

    def register(self, db: Session, data: UserRegister) -> User:
        # Проверяем уникальность телефона
        if db.query(User).filter(User.phone == data.phone).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким номером телефона уже зарегистрирован",
            )

        user = User(
            phone=data.phone,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            region=data.region,
            village=data.village,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # ── Вход ──────────────────────────────────────────────────────────────────

    def login(self, db: Session, data: UserLogin) -> TokenPair:
        user = db.query(User).filter(User.phone == data.phone).first()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный номер телефона или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт заблокирован. Обратитесь в поддержку.",
            )

        # Обновляем время последнего входа
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()

        return TokenPair(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
        )

    # ── Обновление токена ─────────────────────────────────────────────────────

    def refresh(self, db: Session, refresh_token: str) -> TokenPair:
        credentials_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh-токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise credentials_exc
            user_id: int = int(payload["sub"])
        except (JWTError, KeyError, ValueError):
            raise credentials_exc

        user = db.get(User, user_id)
        if not user or not user.is_active:
            raise credentials_exc

        return TokenPair(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
        )

    # ── Получение пользователя по токену ─────────────────────────────────────

    def get_current_user(self, db: Session, token: str) -> User:
        credentials_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить учётные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise credentials_exc
            user_id: int = int(payload["sub"])
        except (JWTError, KeyError, ValueError):
            raise credentials_exc

        user = db.get(User, user_id)
        if not user or not user.is_active:
            raise credentials_exc
        return user


user_service = UserService()
