import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import (
    Referral, Patient, Facility, CarePath, CarePathEvent, CareTask,
    Notification, AuditEvent, ReferralStatus, CarePathState, TaskStatus,
    ReferralUrgency
)
from app.schemas.schemas import (
    ReferralCreate, ReferralOut, RerouteRequest
)
from app.core.auth import get_current_user
from app.models.models import User

router = APIRouter()

NBA_MAP = {
    CarePathState.REFERRAL_CREATED: "Await facility acceptance",
    CarePathState.FACILITY_ACCEPTED: "Arrange patient transport",
    CarePathState.EN_ROUTE: "Confirm patient arrival at destination",
    CarePathState.ARRIVED: "Initiate treatment protocol",
}


def _gen_referral_code(db: Session) -> str:
    count = db.query(Referral).count() + 1
    return f"REF-2026-{count:05d}"


@router.get("", response_model=List[ReferralOut])
def list_referrals(
    status: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    facility_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Referral)
    if status:
        try:
            q = q.filter(Referral.status == ReferralStatus(status))
        except ValueError:
            pass
    if urgency:
        try:
            q = q.filter(Referral.urgency == ReferralUrgency(urgency))
        except ValueError:
            pass
    if facility_id:
        q = q.filter(
            (Referral.destination_facility_id == facility_id) |
            (Referral.origin_facility_id == facility_id)
        )
    return q.order_by(Referral.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=ReferralOut, status_code=201)
def create_referral(
    data: ReferralCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not p:
        raise HTTPException(404, "Patient not found")
    dest = db.query(Facility).filter(Facility.id == data.destination_facility_id).first()
    if not dest:
        raise HTTPException(404, "Destination facility not found")

    ref = Referral(
        id=str(uuid.uuid4()),
        referral_code=_gen_referral_code(db),
        patient_id=data.patient_id,
        origin_facility_id=data.origin_facility_id,
        destination_facility_id=data.destination_facility_id,
        referred_by=current_user.id,
        status=ReferralStatus.PENDING,
        urgency=data.urgency,
        reason=data.reason,
        clinical_notes=data.clinical_notes,
        required_specialty=data.required_specialty,
        expected_arrival=datetime.utcnow() + timedelta(hours=2),
    )
    db.add(ref)

    # Transition CarePath
    cp = db.query(CarePath).filter(CarePath.patient_id == data.patient_id).first()
    if cp:
        old_state = cp.current_state
        cp.current_state = CarePathState.REFERRAL_CREATED
        cp.next_best_action = "Await facility acceptance"
        p.current_state = CarePathState.REFERRAL_CREATED
        db.add(CarePathEvent(
            carepath_id=cp.id,
            from_state=old_state,
            to_state=CarePathState.REFERRAL_CREATED,
            event_type="REFERRAL_CREATED",
            description=f"Referral to {dest.name} created",
            performed_by=current_user.id,
        ))

    # Create task for destination facility staff
    db.add(CareTask(
        patient_id=data.patient_id,
        assigned_to=current_user.id,
        title=f"Confirm referral acceptance from {dest.name}",
        task_type="REFERRAL_CONFIRM",
        status=TaskStatus.OPEN,
        priority="HIGH",
        due_at=datetime.utcnow() + timedelta(minutes=30),
    ))

    db.add(AuditEvent(
        user_id=current_user.id,
        patient_id=data.patient_id,
        event_type="REFERRAL_CREATED",
        entity_type="Referral",
        description=f"Referral created to {dest.name}",
    ))
    db.commit()
    db.refresh(ref)
    return ref


@router.get("/{referral_id}", response_model=ReferralOut)
def get_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(404, "Referral not found")
    return ref


@router.post("/{referral_id}/accept", response_model=ReferralOut)
def accept_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(404, "Referral not found")
    ref.status = ReferralStatus.ACCEPTED
    ref.accepted_at = datetime.utcnow()

    p = db.query(Patient).filter(Patient.id == ref.patient_id).first()
    cp = db.query(CarePath).filter(CarePath.patient_id == ref.patient_id).first()
    if cp and p:
        old = cp.current_state
        cp.current_state = CarePathState.FACILITY_ACCEPTED
        cp.next_best_action = "Arrange patient transport"
        p.current_state = CarePathState.FACILITY_ACCEPTED
        db.add(CarePathEvent(
            carepath_id=cp.id, from_state=old, to_state=CarePathState.FACILITY_ACCEPTED,
            event_type="REFERRAL_ACCEPTED",
            description=f"Referral accepted by {current_user.name}",
            performed_by=current_user.id,
        ))

    db.add(AuditEvent(
        user_id=current_user.id, patient_id=ref.patient_id,
        event_type="REFERRAL_ACCEPTED", entity_type="Referral", entity_id=ref.id,
        description="Referral accepted",
    ))
    db.commit()
    db.refresh(ref)
    return ref


@router.post("/{referral_id}/arrive", response_model=ReferralOut)
def mark_arrived(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(404, "Referral not found")
    ref.status = ReferralStatus.ARRIVED
    ref.arrived_at = datetime.utcnow()

    p = db.query(Patient).filter(Patient.id == ref.patient_id).first()
    cp = db.query(CarePath).filter(CarePath.patient_id == ref.patient_id).first()
    if cp and p:
        old = cp.current_state
        cp.current_state = CarePathState.ARRIVED
        cp.next_best_action = "Initiate treatment protocol"
        p.current_state = CarePathState.ARRIVED
        p.current_facility_id = ref.destination_facility_id
        db.add(CarePathEvent(
            carepath_id=cp.id, from_state=old, to_state=CarePathState.ARRIVED,
            event_type="PATIENT_ARRIVED",
            description="Patient arrived at destination facility",
            performed_by=current_user.id,
        ))

    db.commit()
    db.refresh(ref)
    return ref


@router.post("/{referral_id}/complete", response_model=ReferralOut)
def complete_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(404, "Referral not found")
    ref.status = ReferralStatus.COMPLETED
    ref.completed_at = datetime.utcnow()

    p = db.query(Patient).filter(Patient.id == ref.patient_id).first()
    cp = db.query(CarePath).filter(CarePath.patient_id == ref.patient_id).first()
    if cp and p:
        old = cp.current_state
        cp.current_state = CarePathState.TREATED
        cp.next_best_action = "Create discharge summary and schedule reverse referral"
        p.current_state = CarePathState.TREATED
        db.add(CarePathEvent(
            carepath_id=cp.id, from_state=old, to_state=CarePathState.TREATED,
            event_type="TREATMENT_COMPLETED",
            description="Treatment completed. Referral closed.",
            performed_by=current_user.id,
        ))

    db.commit()
    db.refresh(ref)
    return ref


@router.post("/{referral_id}/reroute", response_model=ReferralOut)
def reroute_referral(
    referral_id: str,
    data: RerouteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(404, "Referral not found")

    new_dest = db.query(Facility).filter(Facility.id == data.new_destination_facility_id).first()
    if not new_dest:
        raise HTTPException(404, "New facility not found")

    # Mark current as rerouted
    ref.status = ReferralStatus.REROUTED
    ref.is_rerouted = True

    # Create new referral
    new_ref = Referral(
        id=str(uuid.uuid4()),
        referral_code=_gen_referral_code(db),
        patient_id=ref.patient_id,
        origin_facility_id=ref.origin_facility_id,
        destination_facility_id=data.new_destination_facility_id,
        referred_by=current_user.id,
        status=ReferralStatus.PENDING,
        urgency=ref.urgency,
        reason=f"REROUTED: {data.reason}",
        clinical_notes=ref.clinical_notes,
        required_specialty=ref.required_specialty,
        previous_referral_id=ref.id,
        expected_arrival=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(new_ref)
    db.flush()

    # Create task + audit
    db.add(CareTask(
        patient_id=ref.patient_id,
        assigned_to=current_user.id,
        title=f"Confirm rerouted referral acceptance — {new_dest.name}",
        task_type="REFERRAL_REROUTE_CONFIRM",
        status=TaskStatus.OPEN,
        priority="URGENT",
        due_at=datetime.utcnow() + timedelta(minutes=15),
        related_referral_id=new_ref.id,
    ))
    db.add(AuditEvent(
        user_id=current_user.id, patient_id=ref.patient_id,
        event_type="REFERRAL_REROUTED", entity_type="Referral", entity_id=ref.id,
        description=f"Rerouted to {new_dest.name}: {data.reason}",
    ))
    db.commit()
    db.refresh(new_ref)
    return new_ref
