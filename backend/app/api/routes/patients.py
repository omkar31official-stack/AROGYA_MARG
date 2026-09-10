import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import (
    Patient, CarePath, CarePathEvent, Observation, Encounter,
    AuditEvent, Notification, CarePathState, RiskEnum, GenderEnum
)
from app.schemas.schemas import (
    PatientCreate, PatientOut, PatientListItem,
    ObservationCreate, ObservationOut,
    EncounterCreate, EncounterOut,
    CarePathOut, CarePathTransitionRequest
)
from app.core.auth import get_current_user
from app.models.models import User
from app.services.carepath import CarePathService

router = APIRouter()

NBA_MAP = {
    CarePathState.IDENTIFIED: "Complete triage assessment",
    CarePathState.TRIAGED: "Schedule PHC consultation",
    CarePathState.CONSULTATION_PENDING: "Complete PHC consultation",
    CarePathState.CONSULTED: "Create referral if required",
    CarePathState.REFERRAL_CREATED: "Await facility acceptance",
    CarePathState.FACILITY_ACCEPTED: "Arrange patient transport",
    CarePathState.EN_ROUTE: "Confirm patient arrival at destination",
    CarePathState.ARRIVED: "Initiate treatment protocol",
    CarePathState.TREATED: "Create discharge and reverse referral",
    CarePathState.BACK_REFERRED: "Schedule ASHA follow-up",
    CarePathState.FOLLOW_UP_DUE: "Complete ASHA follow-up visit",
    CarePathState.CLOSED: "Care journey complete",
}


def _gen_patient_id(db: Session) -> str:
    count = db.query(Patient).count() + 1
    return f"AM-PAT-2026-{count:05d}"


def _gen_care_id(db: Session) -> str:
    count = db.query(Patient).count() + 1
    return f"CARE-2026-{count:05d}"


@router.get("", response_model=List[PatientListItem])
def list_patients(
    search: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Patient).filter(Patient.is_active == True)
    if search:
        q = q.filter(
            Patient.name.ilike(f"%{search}%") |
            Patient.patient_id.ilike(f"%{search}%") |
            Patient.village.ilike(f"%{search}%")
        )
    if risk:
        try:
            q = q.filter(Patient.risk_level == RiskEnum(risk))
        except ValueError:
            pass
    if state:
        try:
            q = q.filter(Patient.current_state == CarePathState(state))
        except ValueError:
            pass
    return q.order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = Patient(
        id=str(uuid.uuid4()),
        patient_id=_gen_patient_id(db),
        care_id=_gen_care_id(db),
        name=data.name,
        age=data.age,
        gender=data.gender,
        phone=data.phone,
        village=data.village,
        household_id=data.household_id,
        asha_id=current_user.id if current_user.role.value == "ASHA" else None,
        known_conditions=data.known_conditions,
        is_pregnant=data.is_pregnant,
        trimester=data.trimester,
        medications=data.medications,
        allergies=data.allergies,
        prev_hospitalization=data.prev_hospitalization,
        risk_level=data.risk_level,
        risk_factors=data.risk_factors,
        current_state=CarePathState.IDENTIFIED,
        consent_given=data.consent_given,
        consent_date=datetime.utcnow() if data.consent_given else None,
    )
    db.add(patient)
    db.flush()

    # Create initial observation if vitals provided
    if any([data.temperature, data.pulse, data.spo2]):
        obs = Observation(
            patient_id=patient.id,
            temperature=data.temperature,
            pulse=data.pulse,
            resp_rate=data.resp_rate,
            spo2=data.spo2,
            bp_systolic=data.bp_systolic,
            bp_diastolic=data.bp_diastolic,
            weight=data.weight,
            symptoms=data.symptoms,
            recorded_by=current_user.id,
        )
        db.add(obs)

    # Create CarePath
    cp = CarePath(
        patient_id=patient.id,
        current_state=CarePathState.IDENTIFIED,
        next_best_action=NBA_MAP[CarePathState.IDENTIFIED],
        responsible_user_id=current_user.id,
        is_active=True,
    )
    db.add(cp)
    db.flush()

    # Initial event
    ev = CarePathEvent(
        carepath_id=cp.id,
        from_state=None,
        to_state=CarePathState.IDENTIFIED,
        event_type="PATIENT_CREATED",
        description=f"Patient registered by {current_user.name}",
        performed_by=current_user.id,
    )
    db.add(ev)

    # Audit
    db.add(AuditEvent(
        user_id=current_user.id,
        patient_id=patient.id,
        event_type="PATIENT_CREATED",
        entity_type="Patient",
        entity_id=patient.id,
        description=f"Patient {patient.name} created",
    ))
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Patient).filter(
        (Patient.id == patient_id) | (Patient.patient_id == patient_id)
    ).first()
    if not p:
        raise HTTPException(404, "Patient not found")
    return p


@router.get("/{patient_id}/carepath", response_model=CarePathOut)
def get_carepath(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(404, "Patient not found")
    cp = db.query(CarePath).filter(CarePath.patient_id == patient_id).first()
    if not cp:
        raise HTTPException(404, "CarePath not found")
    return cp


@router.post("/{patient_id}/carepath/transition", response_model=CarePathOut)
def transition_carepath(
    patient_id: str,
    data: CarePathTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(404, "Patient not found")
    cp = db.query(CarePath).filter(CarePath.patient_id == patient_id).first()
    if not cp:
        raise HTTPException(404, "CarePath not found")

    old_state = cp.current_state
    cp.current_state = data.to_state
    cp.next_best_action = NBA_MAP.get(data.to_state, "Review patient status")
    cp.updated_at = datetime.utcnow()
    p.current_state = data.to_state
    if data.to_state == CarePathState.CLOSED:
        cp.is_active = False
        cp.closed_at = datetime.utcnow()

    ev = CarePathEvent(
        carepath_id=cp.id,
        from_state=old_state,
        to_state=data.to_state,
        event_type=data.event_type,
        description=data.description,
        performed_by=current_user.id,
        metadata=data.metadata,
    )
    db.add(ev)

    db.add(AuditEvent(
        user_id=current_user.id,
        patient_id=patient_id,
        event_type=data.event_type,
        entity_type="CarePath",
        entity_id=cp.id,
        description=f"State transition: {old_state} → {data.to_state}",
        old_value={"state": old_state.value if old_state else None},
        new_value={"state": data.to_state.value},
    ))
    db.commit()
    db.refresh(cp)
    return cp


@router.post("/{patient_id}/observations", response_model=ObservationOut, status_code=201)
def add_observation(
    patient_id: str,
    data: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(404, "Patient not found")
    obs = Observation(
        patient_id=patient_id,
        **data.model_dump(),
        recorded_by=current_user.id,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get("/{patient_id}/observations", response_model=List[ObservationOut])
def get_observations(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Observation).filter(
        Observation.patient_id == patient_id
    ).order_by(Observation.recorded_at.desc()).limit(20).all()


@router.post("/{patient_id}/encounters", response_model=EncounterOut, status_code=201)
def create_encounter(
    patient_id: str,
    data: EncounterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(404, "Patient not found")
    enc = Encounter(
        patient_id=patient_id,
        doctor_id=current_user.id,
        **data.model_dump(),
    )
    db.add(enc)
    db.commit()
    db.refresh(enc)
    return enc
