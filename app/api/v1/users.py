from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_active, require_role
from app.models.user import User, UserRole
from app.schemas.user import (
    UserRegister, UserLogin, UserPublic, UserUpdate,
    TokenPair, RefreshRequest,
)
from app.services.user_service import user_service

router = APIRouter()


# ── AUTH ─────────────────────────────────────────────────────────────────────

@router.post(
    "/auth/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
def register(data: UserRegister, db: Session = Depends(get_db)):
    return user_service.register(db, data)


@router.post(
    "/auth/login",
    response_model=TokenPair,
    summary="Вход по номеру телефона и паролю",
)
def login(data: UserLogin, db: Session = Depends(get_db)):
    return user_service.login(db, data)


@router.post(
    "/auth/login/form",
    response_model=TokenPair,
    include_in_schema=False,  # Только для Swagger UI OAuth2
)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Swagger UI использует username как номер телефона."""
    data = UserLogin(phone=form.username, password=form.password)
    return user_service.login(db, data)


@router.post(
    "/auth/refresh",
    response_model=TokenPair,
    summary="Обновить access-токен через refresh-токен",
)
def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    return user_service.refresh(db, data.refresh_token)


# ── USERS ─────────────────────────────────────────────────────────────────────

@router.get(
    "/users/me",
    response_model=UserPublic,
    summary="Получить данные текущего пользователя",
)
def get_me(current_user: User = Depends(require_active)):
    return current_user


@router.patch(
    "/users/me",
    response_model=UserPublic,
    summary="Обновить профиль текущего пользователя",
)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(require_active),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get(
    "/users",
    response_model=list[UserPublic],
    summary="Список всех пользователей (только admin)",
    dependencies=[Depends(require_role(UserRole.admin))],
)
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.get(
    "/users/{user_id}",
    response_model=UserPublic,
    summary="Профиль пользователя по ID (admin или dispatcher)",
    dependencies=[Depends(require_role(UserRole.admin, UserRole.dispatcher))],
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user
