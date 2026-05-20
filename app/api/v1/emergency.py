from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_active, require_role
from app.models.emergency import EmergencyStatus
from app.models.user import User, UserRole
from app.schemas.emergency import (
    EmergencyCreate, EmergencyPublic,
    EmergencyWithUser, EmergencyStatusUpdate,
)
from app.services.emergency_service import emergency_service

router = APIRouter(prefix="/emergency", tags=["Emergency"])


@router.post(
    "",
    response_model=EmergencyPublic,
    status_code=201,
    summary="Создать экстренный вызов (пациент)",
)
def create_call(
    data: EmergencyCreate,
    current_user: User = Depends(require_active),
    db: Session = Depends(get_db),
):
    return emergency_service.create(db, data, current_user)


@router.get(
    "/my",
    response_model=list[EmergencyPublic],
    summary="Мои вызовы — история (пациент)",
)
def my_calls(
    current_user: User = Depends(require_active),
    db: Session = Depends(get_db),
):
    return emergency_service.get_my_calls(db, current_user.id)


@router.get(
    "/{call_id}",
    response_model=EmergencyPublic,
    summary="Статус конкретного вызова",
)
def get_call(
    call_id: int,
    current_user: User = Depends(require_active),
    db: Session = Depends(get_db),
):
    call = emergency_service.get_or_404(db, call_id)
    # Пациент видит только свои вызовы; диспетчер и админ — все
    if current_user.role == UserRole.patient and call.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Нет доступа к этому вызову")
    return call


@router.get(
    "",
    response_model=list[EmergencyWithUser],
    summary="Все вызовы — для диспетчера и админа",
    dependencies=[Depends(require_role(UserRole.dispatcher, UserRole.admin))],
)
def all_calls(
    status: EmergencyStatus | None = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db),
):
    calls = emergency_service.get_all(db, status)
    result = []
    for c in calls:
        result.append(EmergencyWithUser(
            **{col: getattr(c, col) for col in [
                "id","user_id","type","status","address",
                "description","dispatcher_note","dispatcher_id",
                "created_at","updated_at"
            ]},
            user_name=c.user.full_name,
            user_phone=c.user.phone,
            user_village=c.user.village,
            user_region=c.user.region,
        ))
    return result


@router.patch(
    "/{call_id}/status",
    response_model=EmergencyPublic,
    summary="Обновить статус вызова (диспетчер / админ)",
    dependencies=[Depends(require_role(UserRole.dispatcher, UserRole.admin))],
)
def update_status(
    call_id: int,
    data: EmergencyStatusUpdate,
    current_user: User = Depends(require_active),
    db: Session = Depends(get_db),
):
    return emergency_service.update_status(db, call_id, data, current_user)
