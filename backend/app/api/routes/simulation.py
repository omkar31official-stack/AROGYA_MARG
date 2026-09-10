from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import (
    Facility, Ambulance, Referral, Patient, SimulationScenario,
    FacilityStatus, ReferralStatus, CareTask, Notification, AuditEvent,
    CarePathState, CarePath, CarePathEvent, TaskStatus
)
from app.schemas.schemas import (
    SimulationActivate, SimulationResult, FacilityOut, AmbulanceOut, ReferralOut
)
from app.core.auth import get_current_user
from app.models.models import User

router = APIRouter()


@router.get("/network")
def get_network(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    facilities = db.query(Facility).filter(Facility.is_active == True).all()
    ambulances = db.query(Ambulance).filter(Ambulance.is_active == True).all()
    referrals = db.query(Referral).filter(
        Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.ACCEPTED, ReferralStatus.EN_ROUTE])
    ).limit(20).all()
    patients = db.query(Patient).filter(
        Patient.risk_level.in_(["HIGH", "CRITICAL"]),
        Patient.is_active == True
    ).limit(10).all()

    return {
        "facilities": [FacilityOut.model_validate(f).model_dump() for f in facilities],
        "ambulances": [AmbulanceOut.model_validate(a).model_dump() for a in ambulances],
        "referrals": [ReferralOut.model_validate(r).model_dump() for r in referrals],
        "high_risk_patients": [
            {"id": p.id, "name": p.name, "risk_level": p.risk_level.value,
             "current_state": p.current_state.value, "village": p.village}
            for p in patients
        ],
    }


@router.get("/scenarios")
def list_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(SimulationScenario).all()


@router.post("/scenarios/{scenario_id}/activate")
def activate_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    scenario = db.query(SimulationScenario).filter(SimulationScenario.id == scenario_id).first()
    if not scenario:
        from fastapi import HTTPException
        raise HTTPException(404, "Scenario not found")

    scenario.is_active = True
    scenario.activated_at = datetime.utcnow()

    facility = db.query(Facility).filter(Facility.id == scenario.target_facility_id).first()
    affected_referrals = []
    actions = []

    if facility:
        config = scenario.config or {}
        old_status = facility.status

        if "status" in config:
            facility.status = FacilityStatus(config["status"])
        if "oxygen_available" in config:
            facility.oxygen_available = config["oxygen_available"]
        if "icu_beds" in config:
            facility.icu_beds = config["icu_beds"]
            facility.icu_occupied = config.get("icu_occupied", 0)
        if "occupied_beds" in config:
            facility.occupied_beds = config["occupied_beds"]

        # Recalculate readiness
        facility.readiness_score = max(0, facility.readiness_score - 40)
        actions.append(f"Updated {facility.name} status to {facility.status.value}")

        # Find affected referrals
        refs = db.query(Referral).filter(
            Referral.destination_facility_id == facility.id,
            Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.ACCEPTED, ReferralStatus.EN_ROUTE])
        ).all()

        for ref in refs:
            affected_referrals.append(ref.referral_code)
            # Create urgent task
            db.add(CareTask(
                patient_id=ref.patient_id,
                assigned_to=current_user.id,
                title=f"URGENT: Reroute referral {ref.referral_code} — {facility.name} unavailable",
                task_type="SIMULATION_REROUTE",
                status=TaskStatus.OPEN,
                priority="URGENT",
                due_at=datetime.utcnow(),
                related_referral_id=ref.id,
            ))
            actions.append(f"Created reroute task for referral {ref.referral_code}")

            # Mark patients as facility unavailable
            patient = db.query(Patient).filter(Patient.id == ref.patient_id).first()
            if patient:
                cp = db.query(CarePath).filter(CarePath.patient_id == patient.id).first()
                if cp:
                    old_state = cp.current_state
                    cp.current_state = CarePathState.FACILITY_UNAVAILABLE
                    cp.next_best_action = f"Find alternative facility — {facility.name} unavailable"
                    patient.current_state = CarePathState.FACILITY_UNAVAILABLE
                    db.add(CarePathEvent(
                        carepath_id=cp.id,
                        from_state=old_state,
                        to_state=CarePathState.FACILITY_UNAVAILABLE,
                        event_type="FACILITY_FAILURE_DETECTED",
                        description=f"Facility {facility.name} became unavailable: {scenario.name}",
                        performed_by=current_user.id,
                    ))

        # Find alternative facilities
        alternatives = db.query(Facility).filter(
            Facility.id != facility.id,
            Facility.status.in_([FacilityStatus.READY, FacilityStatus.LIMITED]),
            Facility.is_active == True,
        ).limit(3).all()

        db.add(AuditEvent(
            user_id=current_user.id,
            event_type="SIMULATION_ACTIVATED",
            entity_type="Facility",
            entity_id=facility.id,
            description=f"Simulation scenario activated: {scenario.name}",
            old_value={"status": old_status.value},
            new_value={"status": facility.status.value},
        ))

    db.commit()

    facility_out = FacilityOut.model_validate(facility).model_dump() if facility else None
    return {
        "scenario_name": scenario.name,
        "affected_referrals": affected_referrals,
        "affected_facility": facility_out,
        "alternative_facilities": [FacilityOut.model_validate(a).model_dump() for a in (alternatives if facility else [])],
        "actions_taken": actions,
        "notifications_created": len(affected_referrals),
    }


@router.post("/scenarios/reset")
def reset_simulation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset all active simulations."""
    scenarios = db.query(SimulationScenario).filter(SimulationScenario.is_active == True).all()
    for s in scenarios:
        s.is_active = False
        s.activated_at = None

    # Reset Wagholi to READY
    fac = db.query(Facility).filter(Facility.id == "fac-003").first()
    if fac:
        fac.status = FacilityStatus.READY
        fac.icu_beds = 4
        fac.icu_occupied = 2
        fac.oxygen_available = True
        fac.readiness_score = 78

    db.commit()
    return {"message": "All simulations reset"}
