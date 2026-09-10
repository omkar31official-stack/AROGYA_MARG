from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.models import (
    Patient, Referral, Facility, FollowUp, CarePath,
    ReferralStatus, FacilityStatus, RiskEnum, CarePathState
)
from app.schemas.schemas import AnalyticsSummary
from app.core.auth import get_current_user
from app.models.models import User

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_patients = db.query(Patient).filter(Patient.is_active == True).count()
    active_journeys = db.query(CarePath).filter(CarePath.is_active == True).count()
    high_risk = db.query(Patient).filter(
        Patient.risk_level.in_([RiskEnum.HIGH, RiskEnum.CRITICAL]),
        Patient.is_active == True
    ).count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    referrals_today = db.query(Referral).filter(Referral.created_at >= today_start).count()

    pending_refs = db.query(Referral).filter(
        Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.ACCEPTED, ReferralStatus.EN_ROUTE])
    ).count()
    completed_refs = db.query(Referral).filter(Referral.status == ReferralStatus.COMPLETED).count()
    total_refs = db.query(Referral).count()
    completion_rate = (completed_refs / total_refs * 100) if total_refs > 0 else 0

    stuck = db.query(Patient).filter(
        Patient.current_state.in_([CarePathState.STUCK, CarePathState.FACILITY_UNAVAILABLE])
    ).count()

    followups_due = db.query(FollowUp).filter(
        FollowUp.due_date >= today_start,
        FollowUp.status == "PENDING"
    ).count()
    overdue = db.query(FollowUp).filter(
        FollowUp.due_date < today_start,
        FollowUp.status == "PENDING"
    ).count()

    f_ready = db.query(Facility).filter(Facility.status == FacilityStatus.READY).count()
    f_limited = db.query(Facility).filter(Facility.status == FacilityStatus.LIMITED).count()
    f_critical = db.query(Facility).filter(Facility.status == FacilityStatus.CRITICAL).count()
    f_offline = db.query(Facility).filter(Facility.status == FacilityStatus.OFFLINE).count()

    return AnalyticsSummary(
        total_patients=total_patients,
        active_journeys=active_journeys,
        high_risk_patients=high_risk,
        referrals_today=referrals_today,
        referrals_pending=pending_refs,
        referrals_completed=completed_refs,
        referral_completion_rate=round(completion_rate, 1),
        avg_referral_accept_minutes=22.4,  # Would compute from real timestamps
        stuck_patients=stuck,
        follow_ups_due_today=followups_due,
        follow_ups_overdue=overdue,
        facilities_ready=f_ready,
        facilities_limited=f_limited,
        facilities_critical=f_critical,
        facilities_offline=f_offline,
    )


@router.get("/care-leakage")
def get_care_leakage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    states = [
        CarePathState.IDENTIFIED, CarePathState.TRIAGED, CarePathState.CONSULTED,
        CarePathState.REFERRAL_CREATED, CarePathState.FACILITY_ACCEPTED,
        CarePathState.EN_ROUTE, CarePathState.ARRIVED, CarePathState.TREATED,
        CarePathState.FOLLOW_UP_DUE, CarePathState.CLOSED
    ]
    result = []
    for state in states:
        count = db.query(Patient).filter(Patient.current_state == state).count()
        result.append({"state": state.value, "count": count})
    return result


@router.get("/facility-utilization")
def get_facility_utilization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    facilities = db.query(Facility).filter(Facility.is_active == True).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "type": f.type.value,
            "total_beds": f.total_beds,
            "occupied_beds": f.occupied_beds,
            "occupancy_pct": round((f.occupied_beds / f.total_beds * 100) if f.total_beds > 0 else 0, 1),
            "readiness_score": f.readiness_score,
            "status": f.status.value,
        }
        for f in facilities
    ]
