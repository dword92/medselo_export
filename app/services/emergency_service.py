from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.emergency import EmergencyCall, EmergencyStatus
from app.models.user import User, UserRole
from app.schemas.emergency import EmergencyCreate, EmergencyStatusUpdate

# Допустимые переходы статусов
ALLOWED_TRANSITIONS: dict[EmergencyStatus, list[EmergencyStatus]] = {
    EmergencyStatus.new:        [EmergencyStatus.accepted],
    EmergencyStatus.accepted:   [EmergencyStatus.dispatched],
    EmergencyStatus.dispatched: [EmergencyStatus.arrived],
    EmergencyStatus.arrived:    [EmergencyStatus.closed],
    EmergencyStatus.closed:     [],
}


class EmergencyService:

    def create(self, db: Session, data: EmergencyCreate, current_user: User) -> EmergencyCall:
        # Если адрес не уточнён — берём из профиля
        address = data.address.strip()
        if not address:
            parts = filter(None, [current_user.village, current_user.region])
            address = ", ".join(parts) or "Адрес не указан"

        call = EmergencyCall(
            user_id=current_user.id,
            type=data.type,
            address=address,
            description=data.description or None,
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        return call

    def get_my_calls(self, db: Session, user_id: int) -> list[EmergencyCall]:
        return (
            db.query(EmergencyCall)
            .filter(EmergencyCall.user_id == user_id)
            .order_by(EmergencyCall.created_at.desc())
            .all()
        )

    def get_all(
        self,
        db: Session,
        status: EmergencyStatus | None = None,
    ) -> list[EmergencyCall]:
        q = db.query(EmergencyCall)
        if status:
            q = q.filter(EmergencyCall.status == status)
        return q.order_by(EmergencyCall.created_at.desc()).all()

    def get_or_404(self, db: Session, call_id: int) -> EmergencyCall:
        call = db.get(EmergencyCall, call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Вызов не найден")
        return call

    def update_status(
        self,
        db: Session,
        call_id: int,
        data: EmergencyStatusUpdate,
        dispatcher: User,
    ) -> EmergencyCall:
        call = self.get_or_404(db, call_id)

        allowed = ALLOWED_TRANSITIONS.get(call.status, [])
        if data.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Нельзя перевести вызов из '{call.status}' в '{data.status}'. "
                    f"Допустимо: {[s.value for s in allowed] or 'нет переходов'}"
                ),
            )

        call.status = data.status
        if data.dispatcher_note:
            call.dispatcher_note = data.dispatcher_note
        call.dispatcher_id = dispatcher.id

        db.commit()
        db.refresh(call)
        return call


emergency_service = EmergencyService()
