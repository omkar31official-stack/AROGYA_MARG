from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import CareTask, Notification, FollowUp, TaskStatus
from app.schemas.schemas import TaskOut, NotificationOut, FollowUpOut, FollowUpCreate, FollowUpComplete
from app.core.auth import get_current_user
from app.models.models import User
from datetime import datetime

router = APIRouter()


@router.get("/tasks", response_model=List[TaskOut])
def get_tasks(
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(CareTask).filter(CareTask.assigned_to == current_user.id)
    if status:
        try:
            q = q.filter(CareTask.status == TaskStatus(status))
        except ValueError:
            pass
    return q.order_by(CareTask.due_at.asc()).limit(50).all()


@router.patch("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(CareTask).filter(CareTask.id == task_id).first()
    if task:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return task


@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()


@router.patch("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    n = db.query(Notification).filter(Notification.id == notif_id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"status": "ok"}


@router.get("/follow-ups", response_model=List[FollowUpOut])
def get_follow_ups(
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(FollowUp).filter(FollowUp.assigned_to == current_user.id)
    if status:
        q = q.filter(FollowUp.status == status)
    return q.order_by(FollowUp.due_date.asc()).all()


@router.post("/follow-ups/{followup_id}/complete", response_model=FollowUpOut)
def complete_follow_up(
    followup_id: str,
    data: FollowUpComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fu = db.query(FollowUp).filter(FollowUp.id == followup_id).first()
    if fu:
        fu.status = "COMPLETED"
        fu.completed_at = datetime.utcnow()
        fu.notes = data.notes
        fu.vitals = data.vitals
        fu.medication_adherence = data.medication_adherence
        fu.recovery_status = data.recovery_status
        db.commit()
        db.refresh(fu)
    return fu
