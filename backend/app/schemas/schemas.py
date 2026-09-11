from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime
from app.models.models import (
    RoleEnum, GenderEnum, RiskEnum, CarePathState, FacilityType,
    FacilityStatus, ReferralStatus, ReferralUrgency, TaskStatus,
    AmbulanceStatus
)


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum
    facility_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ─── User ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    employee_id: str
    name: str
    email: str
    phone: Optional[str]
    role: RoleEnum
    facility_id: Optional[str]
    district: Optional[str]
    taluka: Optional[str]
    village: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Facility ─────────────────────────────────────────────────────────────────

class FacilityOut(BaseModel):
    id: str
    facility_code: str
    name: str
    type: FacilityType
    status: FacilityStatus
    address: Optional[str]
    village: Optional[str]
    taluka: Optional[str]
    district: str
    lat: float
    lng: float
    phone: Optional[str]
    readiness_score: int
    total_beds: int
    occupied_beds: int
    icu_beds: int
    icu_occupied: int
    ventilators: int
    oxygen_available: bool
    blood_bank: bool
    diagnostics: List[str]
    specialists: List[str]
    is_active: bool
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class FacilityUpdateRequest(BaseModel):
    status: Optional[FacilityStatus]
    total_beds: Optional[int]
    occupied_beds: Optional[int]
    icu_beds: Optional[int]
    icu_occupied: Optional[int]
    oxygen_available: Optional[bool]
    blood_bank: Optional[bool]
    readiness_score: Optional[int]


# ─── Patient ──────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: GenderEnum
    phone: Optional[str] = None
    village: str
    household_id: Optional[str] = None
    known_conditions: List[str] = []
    is_pregnant: bool = False
    trimester: Optional[int] = None
    medications: List[str] = []
    allergies: List[str] = []
    prev_hospitalization: bool = False
    risk_level: RiskEnum = RiskEnum.LOW
    risk_factors: List[str] = []
    symptoms: List[str] = []
    temperature: Optional[float] = None
    pulse: Optional[int] = None
    resp_rate: Optional[int] = None
    spo2: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    weight: Optional[float] = None
    consent_given: bool = False


class PatientOut(BaseModel):
    id: str
    patient_id: str
    care_id: str
    name: str
    age: int
    gender: GenderEnum
    phone: Optional[str]
    village: str
    district: str
    asha_id: Optional[str]
    known_conditions: List[Any]
    is_pregnant: bool
    trimester: Optional[int]
    medications: List[Any]
    allergies: List[Any]
    risk_level: RiskEnum
    risk_factors: List[Any]
    current_state: CarePathState
    current_facility_id: Optional[str]
    consent_given: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PatientListItem(BaseModel):
    id: str
    patient_id: str
    care_id: str
    name: str
    age: int
    gender: GenderEnum
    village: str
    risk_level: RiskEnum
    current_state: CarePathState
    is_pregnant: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Observation ──────────────────────────────────────────────────────────────

class ObservationCreate(BaseModel):
    temperature: Optional[float]
    pulse: Optional[int]
    resp_rate: Optional[int]
    spo2: Optional[int]
    bp_systolic: Optional[int]
    bp_diastolic: Optional[int]
    weight: Optional[float]
    symptoms: List[str] = []
    risk_indicators: List[str] = []


class ObservationOut(BaseModel):
    id: str
    patient_id: str
    temperature: Optional[float]
    pulse: Optional[int]
    resp_rate: Optional[int]
    spo2: Optional[int]
    bp_systolic: Optional[int]
    bp_diastolic: Optional[int]
    weight: Optional[float]
    symptoms: List[Any]
    risk_indicators: List[Any]
    recorded_at: datetime

    class Config:
        from_attributes = True


# ─── CarePath ─────────────────────────────────────────────────────────────────

class CarePathOut(BaseModel):
    id: str
    patient_id: str
    current_state: CarePathState
    next_best_action: Optional[str]
    responsible_user_id: Optional[str]
    deadline: Optional[datetime]
    started_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    events: List["CarePathEventOut"] = []

    class Config:
        from_attributes = True


class CarePathEventOut(BaseModel):
    id: str
    from_state: Optional[CarePathState]
    to_state: CarePathState
    event_type: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CarePathTransitionRequest(BaseModel):
    to_state: CarePathState
    event_type: str
    description: Optional[str]
    metadata: dict = {}


# ─── Referral ─────────────────────────────────────────────────────────────────

class ReferralCreate(BaseModel):
    patient_id: str
    origin_facility_id: Optional[str]
    destination_facility_id: str
    urgency: ReferralUrgency = ReferralUrgency.ROUTINE
    reason: str
    clinical_notes: Optional[str]
    required_specialty: Optional[str]


class ReferralOut(BaseModel):
    id: str
    referral_code: str
    patient_id: str
    origin_facility_id: Optional[str]
    destination_facility_id: str
    referred_by: str
    status: ReferralStatus
    urgency: ReferralUrgency
    reason: str
    clinical_notes: Optional[str]
    required_specialty: Optional[str]
    ambulance_id: Optional[str]
    created_at: datetime
    accepted_at: Optional[datetime]
    arrived_at: Optional[datetime]
    completed_at: Optional[datetime]
    expected_arrival: Optional[datetime]
    is_rerouted: bool

    class Config:
        from_attributes = True


class RerouteRequest(BaseModel):
    new_destination_facility_id: str
    reason: str


# ─── Encounter ────────────────────────────────────────────────────────────────

class EncounterCreate(BaseModel):
    facility_id: Optional[str]
    encounter_type: str
    chief_complaint: str
    diagnosis: Optional[str]
    treatment_notes: Optional[str]


class EncounterOut(BaseModel):
    id: str
    patient_id: str
    facility_id: Optional[str]
    encounter_type: str
    chief_complaint: str
    diagnosis: Optional[str]
    treatment_notes: Optional[str]
    encounter_date: datetime

    class Config:
        from_attributes = True


# ─── Task ─────────────────────────────────────────────────────────────────────

class TaskOut(BaseModel):
    id: str
    patient_id: Optional[str]
    assigned_to: str
    title: str
    description: Optional[str]
    task_type: Optional[str]
    status: TaskStatus
    priority: str
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    related_referral_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Analytics ────────────────────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_patients: int
    active_journeys: int
    high_risk_patients: int
    referrals_today: int
    referrals_pending: int
    referrals_completed: int
    referral_completion_rate: float
    avg_referral_accept_minutes: float
    stuck_patients: int
    follow_ups_due_today: int
    follow_ups_overdue: int
    facilities_ready: int
    facilities_limited: int
    facilities_critical: int
    facilities_offline: int


# ─── Network ──────────────────────────────────────────────────────────────────

class NetworkSummary(BaseModel):
    facilities: List[FacilityOut]
    ambulances: List["AmbulanceOut"]
    active_referrals: List[ReferralOut]


class AmbulanceOut(BaseModel):
    id: str
    vehicle_number: str
    vehicle_type: str
    status: AmbulanceStatus
    base_facility_id: Optional[str]
    driver_name: Optional[str]
    current_lat: Optional[float]
    current_lng: Optional[float]
    destination_lat: Optional[float]
    destination_lng: Optional[float]
    eta_minutes: Optional[int]
    speed_kmph: Optional[float]
    patient_on_board: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# ─── Simulation ───────────────────────────────────────────────────────────────

class SimulationActivate(BaseModel):
    scenario_id: str


class SimulationResult(BaseModel):
    scenario_name: str
    affected_referrals: List[str]
    alternative_facilities: List[FacilityOut]
    actions_taken: List[str]
    notifications_created: int


# ─── Notification ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: str
    title: str
    message: Optional[str]
    type: Optional[str]
    severity: str
    is_read: bool
    action_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Follow-up ────────────────────────────────────────────────────────────────

class FollowUpCreate(BaseModel):
    due_date: datetime
    reason: str


class FollowUpComplete(BaseModel):
    notes: str
    vitals: dict = {}
    medication_adherence: Optional[bool]
    recovery_status: Optional[str]


class FollowUpOut(BaseModel):
    id: str
    patient_id: str
    assigned_to: str
    due_date: datetime
    reason: str
    notes: Optional[str]
    status: str
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


CarePathOut.model_rebuild()
TokenResponse.model_rebuild()
NetworkSummary.model_rebuild()
