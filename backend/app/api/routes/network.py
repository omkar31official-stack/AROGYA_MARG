import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Facility, FacilityStatus
from app.schemas.schemas import FacilityOut
from app.core.auth import get_current_user
from app.models.models import User

router = APIRouter()


def _haversine(lat1, lng1, lat2, lng2) -> float:
    """Distance in km between two coordinates."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2*R*math.asin(math.sqrt(a))


def _score_facility(facility: Facility, requirements: dict, distance_km: float) -> dict:
    """Score a facility 0–100 based on patient requirements and availability."""
    score = 0
    reasons = []
    disqualifiers = []

    # Availability checks
    if facility.status == FacilityStatus.OFFLINE:
        return {"score": 0, "match_pct": 0, "reasons": [], "disqualifiers": ["Facility offline"]}
    if facility.status == FacilityStatus.CRITICAL:
        score -= 30
        disqualifiers.append("Facility at critical capacity")

    # Beds
    available_beds = facility.total_beds - facility.occupied_beds
    if available_beds > 5:
        score += 20
        reasons.append(f"{available_beds} beds available")
    elif available_beds > 0:
        score += 10
        reasons.append(f"Only {available_beds} beds available")
    else:
        disqualifiers.append("No beds available")

    # ICU
    if requirements.get("needs_icu"):
        available_icu = facility.icu_beds - facility.icu_occupied
        if available_icu > 0:
            score += 25
            reasons.append(f"ICU available ({available_icu} beds)")
        else:
            score -= 25
            disqualifiers.append("No ICU available")

    # Oxygen
    if requirements.get("needs_oxygen"):
        if facility.oxygen_available:
            score += 15
            reasons.append("Oxygen available")
        else:
            score -= 20
            disqualifiers.append("No oxygen supply")
    elif facility.oxygen_available:
        score += 10

    # Blood
    if requirements.get("needs_blood"):
        if facility.blood_bank:
            score += 15
            reasons.append("Blood bank available")
        else:
            score -= 10
            disqualifiers.append("No blood bank")
    elif facility.blood_bank:
        score += 5

    # Specialty
    required_specialty = requirements.get("specialty")
    if required_specialty:
        if required_specialty in (facility.specialists or []):
            score += 20
            reasons.append(f"{required_specialty} specialist available")
        else:
            score -= 15
            disqualifiers.append(f"{required_specialty} specialist not available")

    # Diagnostics
    required_diagnostics = requirements.get("diagnostics", [])
    matched_diag = [d for d in required_diagnostics if d in (facility.diagnostics or [])]
    if required_diagnostics:
        match_ratio = len(matched_diag) / len(required_diagnostics)
        score += int(match_ratio * 15)
        if matched_diag:
            reasons.append(f"Diagnostics: {', '.join(matched_diag)}")

    # Distance penalty
    if distance_km < 10:
        score += 15
        reasons.append(f"{distance_km:.1f} km away")
    elif distance_km < 30:
        score += 5
    elif distance_km > 60:
        score -= 10

    match_pct = max(0, min(100, score + 50))
    travel_time = int((distance_km / 50) * 60)  # ~50km/h avg

    return {
        "score": score,
        "match_pct": match_pct,
        "distance_km": round(distance_km, 1),
        "travel_time_min": travel_time,
        "reasons": reasons,
        "disqualifiers": disqualifiers,
    }


@router.get("/route", response_model=List[dict])
def smart_facility_route(
    origin_lat: float = Query(...),
    origin_lng: float = Query(...),
    needs_icu: bool = Query(False),
    needs_oxygen: bool = Query(False),
    needs_blood: bool = Query(False),
    specialty: Optional[str] = Query(None),
    diagnostics: Optional[str] = Query(None),
    facility_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requirements = {
        "needs_icu": needs_icu,
        "needs_oxygen": needs_oxygen,
        "needs_blood": needs_blood,
        "specialty": specialty,
        "diagnostics": [d.strip() for d in diagnostics.split(",")] if diagnostics else [],
    }

    q = db.query(Facility).filter(Facility.is_active == True)
    if facility_type:
        from app.models.models import FacilityType
        try:
            q = q.filter(Facility.type == FacilityType(facility_type))
        except ValueError:
            pass

    facilities = q.all()
    results = []
    for f in facilities:
        dist = _haversine(origin_lat, origin_lng, f.lat, f.lng)
        if dist > 100:
            continue
        scoring = _score_facility(f, requirements, dist)
        results.append({
            "facility": {
                "id": f.id,
                "name": f.name,
                "type": f.type.value,
                "status": f.status.value,
                "lat": f.lat,
                "lng": f.lng,
                "readiness_score": f.readiness_score,
                "total_beds": f.total_beds,
                "occupied_beds": f.occupied_beds,
                "icu_beds": f.icu_beds,
                "icu_occupied": f.icu_occupied,
                "oxygen_available": f.oxygen_available,
                "blood_bank": f.blood_bank,
                "diagnostics": f.diagnostics or [],
                "specialists": f.specialists or [],
            },
            **scoring,
        })

    results.sort(key=lambda x: (-x["match_pct"], x["distance_km"]))
    return results[:5]
