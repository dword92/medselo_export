from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.user_service import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/form")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    return user_service.get_current_user(db, token)


def require_active(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт неактивен")
    return current_user


def require_role(*roles: UserRole):
    """Фабрика зависимостей: require_role(UserRole.admin, UserRole.dispatcher)."""
    def checker(current_user: User = Depends(require_active)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещён. Требуется роль: {', '.join(r.value for r in roles)}",
            )
        return current_user
    return checker
