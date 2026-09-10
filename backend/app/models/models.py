import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, Enum,
    ForeignKey, JSON, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ─── Enums ───────────────────────────────────────────────────────────────────

class RoleEnum(str, enum.Enum):
    ASHA = "ASHA"
    CHO = "CHO"
    PHC_DOCTOR = "PHC_DOCTOR"
    HOSPITAL_STAFF = "HOSPITAL_STAFF"
    SPECIALIST = "SPECIALIST"
    DISTRICT_ADMIN = "DISTRICT_ADMIN"


class GenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class RiskEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CarePathState(str, enum.Enum):
    IDENTIFIED = "IDENTIFIED"
    TRIAGED = "TRIAGED"
    CONSULTATION_PENDING = "CONSULTATION_PENDING"
    CONSULTED = "CONSULTED"
    REFERRAL_CREATED = "REFERRAL_CREATED"
    FACILITY_ACCEPTED = "FACILITY_ACCEPTED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    TREATED = "TREATED"
    BACK_REFERRED = "BACK_REFERRED"
    FOLLOW_UP_DUE = "FOLLOW_UP_DUE"
    CLOSED = "CLOSED"
    STUCK = "STUCK"
    NO_SHOW = "NO_SHOW"
    ESCALATED = "ESCALATED"
    FACILITY_UNAVAILABLE = "FACILITY_UNAVAILABLE"


class FacilityType(str, enum.Enum):
    ASHA_WORKER = "ASHA_WORKER"
    AROGYA_MANDIR = "AROGYA_MANDIR"
    SUB_CENTRE = "SUB_CENTRE"
    PHC = "PHC"
    CHC = "CHC"
    RURAL_HOSPITAL = "RURAL_HOSPITAL"
    DISTRICT_HOSPITAL = "DISTRICT_HOSPITAL"
    DIAGNOSTIC_CENTRE = "DIAGNOSTIC_CENTRE"
    BLOOD_BANK = "BLOOD_BANK"


class FacilityStatus(str, enum.Enum):
    READY = "READY"
    LIMITED = "LIMITED"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"


class ReferralStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REROUTED = "REROUTED"


class ReferralUrgency(str, enum.Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class TaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AmbulanceStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    DISPATCHED = "DISPATCHED"
    EN_ROUTE = "EN_ROUTE"
    AT_SCENE = "AT_SCENE"
    TRANSPORTING = "TRANSPORTING"
    OFFLINE = "OFFLINE"


# ─── Models ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    employee_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    facility_id = Column(String, ForeignKey("facilities.id"), nullable=True)
    district = Column(String, default="Pune")
    taluka = Column(String)
    village = Column(String)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    facility = relationship("Facility", back_populates="staff", foreign_keys=[facility_id])
    patients_assigned = relationship("Patient", back_populates="asha_worker", foreign_keys="Patient.asha_id")
    audit_events = relationship("AuditEvent", back_populates="user")
    tasks = relationship("CareTask", back_populates="assigned_to_user", foreign_keys="CareTask.assigned_to")


class Household(Base):
    __tablename__ = "households"
    id = Column(String, primary_key=True, default=gen_uuid)
    household_code = Column(String, unique=True, index=True)
    address = Column(Text)
    village = Column(String)
    taluka = Column(String)
    district = Column(String, default="Pune")
    lat = Column(Float)
    lng = Column(Float)
    family_members_count = Column(Integer, default=1)
    primary_contact_name = Column(String)
    primary_contact_phone = Column(String)
    asha_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    patients = relationship("Patient", back_populates="household")


class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, unique=True, index=True)  # AM-PAT-2026-XXXXX
    care_id = Column(String, unique=True, index=True)     # CARE-2026-XXXXX
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(Enum(GenderEnum))
    phone = Column(String)
    village = Column(String)
    district = Column(String, default="Pune")
    household_id = Column(String, ForeignKey("households.id"))
    asha_id = Column(String, ForeignKey("users.id"))
    # Health profile
    known_conditions = Column(JSON, default=list)
    is_pregnant = Column(Boolean, default=False)
    trimester = Column(Integer, nullable=True)
    medications = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    prev_hospitalization = Column(Boolean, default=False)
    # Risk
    risk_level = Column(Enum(RiskEnum), default=RiskEnum.LOW)
    risk_factors = Column(JSON, default=list)
    # Current state
    current_state = Column(Enum(CarePathState), default=CarePathState.IDENTIFIED)
    current_facility_id = Column(String, ForeignKey("facilities.id"), nullable=True)
    # Consent
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    # FHIR-compatible fields
    abha_id = Column(String, nullable=True)
    fhir_patient_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    household = relationship("Household", back_populates="patients")
    asha_worker = relationship("User", back_populates="patients_assigned", foreign_keys=[asha_id])
    current_facility = relationship("Facility", foreign_keys=[current_facility_id])
    carepath = relationship("CarePath", back_populates="patient", uselist=False)
    encounters = relationship("Encounter", back_populates="patient")
    observations = relationship("Observation", back_populates="patient")
    referrals = relationship("Referral", back_populates="patient")
    follow_ups = relationship("FollowUp", back_populates="patient")
    tasks = relationship("CareTask", back_populates="patient")
    notifications = relationship("Notification", back_populates="patient")
    audit_events = relationship("AuditEvent", back_populates="patient")


class Facility(Base):
    __tablename__ = "facilities"
    id = Column(String, primary_key=True, default=gen_uuid)
    facility_code = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(FacilityType), nullable=False)
    status = Column(Enum(FacilityStatus), default=FacilityStatus.READY)
    address = Column(Text)
    village = Column(String)
    taluka = Column(String)
    district = Column(String, default="Pune")
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    phone = Column(String)
    readiness_score = Column(Integer, default=100)  # 0-100
    # Capacity
    total_beds = Column(Integer, default=0)
    occupied_beds = Column(Integer, default=0)
    icu_beds = Column(Integer, default=0)
    icu_occupied = Column(Integer, default=0)
    ventilators = Column(Integer, default=0)
    # Availability flags
    oxygen_available = Column(Boolean, default=True)
    blood_bank = Column(Boolean, default=False)
    # Diagnostics
    diagnostics = Column(JSON, default=list)  # ["CBC", "X-Ray", "Ultrasound", "CT"]
    # Specialists
    specialists = Column(JSON, default=list)  # ["Medicine", "Pediatrics"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    staff = relationship("User", back_populates="facility", foreign_keys="User.facility_id")
    referrals_incoming = relationship("Referral", back_populates="destination_facility", foreign_keys="Referral.destination_facility_id")
    referrals_outgoing = relationship("Referral", back_populates="origin_facility", foreign_keys="Referral.origin_facility_id")
    ambulances = relationship("Ambulance", back_populates="base_facility")


class CarePath(Base):
    __tablename__ = "care_paths"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), unique=True, nullable=False)
    current_state = Column(Enum(CarePathState), default=CarePathState.IDENTIFIED)
    next_best_action = Column(Text, nullable=True)
    responsible_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    patient = relationship("Patient", back_populates="carepath")
    events = relationship("CarePathEvent", back_populates="carepath", order_by="CarePathEvent.created_at")
    responsible_user = relationship("User", foreign_keys=[responsible_user_id])


class CarePathEvent(Base):
    __tablename__ = "carepath_events"
    id = Column(String, primary_key=True, default=gen_uuid)
    carepath_id = Column(String, ForeignKey("care_paths.id"), nullable=False)
    from_state = Column(Enum(CarePathState), nullable=True)
    to_state = Column(Enum(CarePathState), nullable=False)
    event_type = Column(String, nullable=False)
    description = Column(Text)
    performed_by = Column(String, ForeignKey("users.id"), nullable=True)
    event_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    carepath = relationship("CarePath", back_populates="events")
    performer = relationship("User", foreign_keys=[performed_by])


class Encounter(Base):
    __tablename__ = "encounters"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    facility_id = Column(String, ForeignKey("facilities.id"), nullable=True)
    doctor_id = Column(String, ForeignKey("users.id"), nullable=True)
    encounter_type = Column(String)  # "FIELD_VISIT", "CONSULTATION", "HOSPITALIZATION"
    chief_complaint = Column(Text)
    diagnosis = Column(Text)
    treatment_notes = Column(Text)
    encounter_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="encounters")
    facility = relationship("Facility")
    doctor = relationship("User", foreign_keys=[doctor_id])
    observations = relationship("Observation", back_populates="encounter")


class Observation(Base):
    __tablename__ = "observations"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(String, ForeignKey("encounters.id"), nullable=True)
    # Vitals
    temperature = Column(Float)   # °F
    pulse = Column(Integer)       # bpm
    resp_rate = Column(Integer)   # breaths/min
    spo2 = Column(Integer)        # %
    bp_systolic = Column(Integer)
    bp_diastolic = Column(Integer)
    weight = Column(Float)        # kg
    symptoms = Column(JSON, default=list)
    risk_indicators = Column(JSON, default=list)
    recorded_by = Column(String, ForeignKey("users.id"))
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="observations")
    encounter = relationship("Encounter", back_populates="observations")
    recorder = relationship("User", foreign_keys=[recorded_by])


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(String, primary_key=True, default=gen_uuid)
    referral_code = Column(String, unique=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    origin_facility_id = Column(String, ForeignKey("facilities.id"), nullable=True)
    destination_facility_id = Column(String, ForeignKey("facilities.id"), nullable=False)
    referred_by = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING)
    urgency = Column(Enum(ReferralUrgency), default=ReferralUrgency.ROUTINE)
    reason = Column(Text)
    clinical_notes = Column(Text)
    required_specialty = Column(String)
    ambulance_id = Column(String, ForeignKey("ambulances.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expected_arrival = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    is_rerouted = Column(Boolean, default=False)
    previous_referral_id = Column(String, ForeignKey("referrals.id"), nullable=True)

    patient = relationship("Patient", back_populates="referrals")
    origin_facility = relationship("Facility", back_populates="referrals_outgoing", foreign_keys=[origin_facility_id])
    destination_facility = relationship("Facility", back_populates="referrals_incoming", foreign_keys=[destination_facility_id])
    referrer = relationship("User", foreign_keys=[referred_by])
    ambulance = relationship("Ambulance", foreign_keys=[ambulance_id])


class FollowUp(Base):
    __tablename__ = "follow_ups"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    assigned_to = Column(String, ForeignKey("users.id"), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String)
    notes = Column(Text)
    vitals = Column(JSON, default=dict)
    medication_adherence = Column(Boolean, nullable=True)
    recovery_status = Column(String, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, COMPLETED, MISSED
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="follow_ups")
    assignee = relationship("User", foreign_keys=[assigned_to])


class CareTask(Base):
    __tablename__ = "care_tasks"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)
    assigned_to = Column(String, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(String, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    task_type = Column(String)  # "REFERRAL_CONFIRM", "FOLLOW_UP", "TRANSPORT", etc
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)
    priority = Column(String, default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    related_referral_id = Column(String, ForeignKey("referrals.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="tasks")
    assigned_to_user = relationship("User", back_populates="tasks", foreign_keys=[assigned_to])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text)
    type = Column(String)  # "REFERRAL", "FOLLOW_UP", "FACILITY", "TASK", "ALERT"
    severity = Column(String, default="INFO")  # INFO, WARNING, ERROR, CRITICAL
    is_read = Column(Boolean, default=False)
    action_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    patient = relationship("Patient", back_populates="notifications")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)
    event_type = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(String)
    description = Column(Text)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_events")
    patient = relationship("Patient", back_populates="audit_events")


class Ambulance(Base):
    __tablename__ = "ambulances"
    id = Column(String, primary_key=True, default=gen_uuid)
    vehicle_number = Column(String, unique=True)
    vehicle_type = Column(String)  # "BLS", "ALS", "HEARSE"
    status = Column(Enum(AmbulanceStatus), default=AmbulanceStatus.AVAILABLE)
    base_facility_id = Column(String, ForeignKey("facilities.id"), nullable=True)
    driver_name = Column(String)
    driver_phone = Column(String)
    current_lat = Column(Float)
    current_lng = Column(Float)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    eta_minutes = Column(Integer, nullable=True)
    speed_kmph = Column(Float, nullable=True)
    patient_on_board = Column(String, ForeignKey("patients.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    base_facility = relationship("Facility", back_populates="ambulances")


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    scenario_type = Column(String)  # "FACILITY_OVERLOADED", "ICU_UNAVAILABLE", etc
    target_facility_id = Column(String, ForeignKey("facilities.id"), nullable=True)
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=False)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
