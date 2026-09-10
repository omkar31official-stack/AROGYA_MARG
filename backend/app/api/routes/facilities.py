from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Facility, FacilityStatus, FacilityType, AuditEvent
from app.schemas.schemas import FacilityOut, FacilityUpdateRequest
from app.core.auth import get_current_user
from app.models.models import User

router = APIRouter()


@router.get("", response_model=List[FacilityOut])
def list_facilities(
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Facility).filter(Facility.is_active == True)
    if type:
        try:
            q = q.filter(Facility.type == FacilityType(type))
        except ValueError:
            pass
    if status:
        try:
            q = q.filter(Facility.status == FacilityStatus(status))
        except ValueError:
            pass
    return q.all()


@router.get("/{facility_id}", response_model=FacilityOut)
def get_facility(
    facility_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    f = db.query(Facility).filter(Facility.id == facility_id).first()
    if not f:
        raise HTTPException(404, "Facility not found")
    return f


@router.patch("/{facility_id}", response_model=FacilityOut)
def update_facility(
    facility_id: str,
    data: FacilityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    f = db.query(Facility).filter(Facility.id == facility_id).first()
    if not f:
        raise HTTPException(404, "Facility not found")
    old_vals = {}
    new_vals = {}
    for field, value in data.model_dump(exclude_none=True).items():
        old_vals[field] = getattr(f, field)
        setattr(f, field, value)
        new_vals[field] = value

    # Recalculate readiness score
    score = 100
    if f.status == FacilityStatus.LIMITED:
        score -= 30
    elif f.status == FacilityStatus.CRITICAL:
        score -= 60
    elif f.status == FacilityStatus.OFFLINE:
        score = 0
    if not f.oxygen_available:
        score -= 20
    if f.total_beds > 0 and (f.occupied_beds / f.total_beds) > 0.9:
        score -= 15
    f.readiness_score = max(0, score)

    db.add(AuditEvent(
        user_id=current_user.id,
        event_type="FACILITY_UPDATED",
        entity_type="Facility",
        entity_id=facility_id,
        description=f"Facility {f.name} updated",
        old_value=old_vals,
        new_value=new_vals,
    ))
    db.commit()
    db.refresh(f)
    return f


@router.get("/{facility_id}/readiness")
def get_readiness(
    facility_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    f = db.query(Facility).filter(Facility.id == facility_id).first()
    if not f:
        raise HTTPException(404, "Facility not found")
    available_beds = f.total_beds - f.occupied_beds
    available_icu = f.icu_beds - f.icu_occupied
    occupancy = (f.occupied_beds / f.total_beds * 100) if f.total_beds > 0 else 0
    return {
        "facility_id": facility_id,
        "readiness_score": f.readiness_score,
        "status": f.status.value,
        "available_beds": available_beds,
        "available_icu": available_icu,
        "occupancy_pct": round(occupancy, 1),
        "oxygen": f.oxygen_available,
        "blood_bank": f.blood_bank,
        "diagnostics": f.diagnostics,
        "specialists": f.specialists,
    }
