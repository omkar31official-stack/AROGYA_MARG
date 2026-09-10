"""
Seed data for Arogya Marg — Pune District / Haveli Taluka
ALL DATA IS SYNTHETIC DEMO DATA. Not live government data.
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import (
    User, Facility, Patient, Household, CarePath, CarePathEvent,
    Referral, FollowUp, CareTask, Notification, AuditEvent, Ambulance,
    SimulationScenario, RoleEnum, GenderEnum, RiskEnum, CarePathState,
    FacilityType, FacilityStatus, ReferralStatus, ReferralUrgency,
    TaskStatus, AmbulanceStatus
)
from app.core.auth import hash_password
import uuid


def gen_uuid():
    return str(uuid.uuid4())


def seed_database(db: Session):
    # ── Check if already seeded ──────────────────────────────────────
    if db.query(User).count() > 0:
        return

    print("🌱 Seeding Arogya Marg database with Pune/Haveli demo data...")

    # ── Facilities (Haveli Taluka, Pune District) ─────────────────────
    facilities_data = [
        {
            "id": "fac-001", "facility_code": "PHC-MANJARI-01",
            "name": "PHC Manjari", "type": FacilityType.PHC,
            "status": FacilityStatus.READY, "village": "Manjari",
            "taluka": "Haveli", "lat": 18.5089, "lng": 73.9634,
            "phone": "020-27451234", "readiness_score": 87,
            "total_beds": 30, "occupied_beds": 18, "icu_beds": 0, "icu_occupied": 0,
            "oxygen_available": True, "blood_bank": False,
            "diagnostics": ["CBC", "Urine", "Blood Sugar", "X-Ray"],
            "specialists": ["Medicine", "Obstetrics"]
        },
        {
            "id": "fac-002", "facility_code": "PHC-KESNAND-01",
            "name": "PHC Kesnand", "type": FacilityType.PHC,
            "status": FacilityStatus.LIMITED, "village": "Kesnand",
            "taluka": "Haveli", "lat": 18.5312, "lng": 73.9891,
            "phone": "020-27451235", "readiness_score": 62,
            "total_beds": 20, "occupied_beds": 16, "icu_beds": 0, "icu_occupied": 0,
            "oxygen_available": True, "blood_bank": False,
            "diagnostics": ["CBC", "Blood Sugar"],
            "specialists": ["Medicine"]
        },
        {
            "id": "fac-003", "facility_code": "RH-WAGHOLI-01",
            "name": "Rural Hospital Wagholi", "type": FacilityType.RURAL_HOSPITAL,
            "status": FacilityStatus.READY, "village": "Wagholi",
            "taluka": "Haveli", "lat": 18.5565, "lng": 73.9841,
            "phone": "020-27451236", "readiness_score": 78,
            "total_beds": 60, "occupied_beds": 35, "icu_beds": 4, "icu_occupied": 2,
            "oxygen_available": True, "blood_bank": False,
            "diagnostics": ["CBC", "X-Ray", "Ultrasound", "ECG"],
            "specialists": ["Medicine", "Pediatrics", "Obstetrics"]
        },
        {
            "id": "fac-004", "facility_code": "RH-LONI-01",
            "name": "Rural Hospital Loni Kalbhor", "type": FacilityType.RURAL_HOSPITAL,
            "status": FacilityStatus.CRITICAL, "village": "Loni Kalbhor",
            "taluka": "Haveli", "lat": 18.4789, "lng": 73.9201,
            "phone": "020-27451237", "readiness_score": 34,
            "total_beds": 40, "occupied_beds": 39, "icu_beds": 2, "icu_occupied": 2,
            "oxygen_available": False, "blood_bank": False,
            "diagnostics": ["CBC"],
            "specialists": ["Medicine"]
        },
        {
            "id": "fac-005", "facility_code": "DH-SASSOON-01",
            "name": "Sassoon District Hospital", "type": FacilityType.DISTRICT_HOSPITAL,
            "status": FacilityStatus.READY, "village": "Pune City",
            "taluka": "Pune", "lat": 18.5195, "lng": 73.8553,
            "phone": "020-26128000", "readiness_score": 92,
            "total_beds": 250, "occupied_beds": 180, "icu_beds": 30, "icu_occupied": 22,
            "oxygen_available": True, "blood_bank": True,
            "diagnostics": ["CBC", "X-Ray", "Ultrasound", "CT", "MRI", "ECG", "Pathology"],
            "specialists": ["Medicine", "Pediatrics", "Obstetrics", "Surgery", "Cardiology", "Neurology", "Orthopedics"]
        },
        {
            "id": "fac-006", "facility_code": "CHC-KHED-01",
            "name": "CHC Khed Shivapur", "type": FacilityType.CHC,
            "status": FacilityStatus.READY, "village": "Khed Shivapur",
            "taluka": "Haveli", "lat": 18.3789, "lng": 73.8123,
            "phone": "020-27451238", "readiness_score": 71,
            "total_beds": 50, "occupied_beds": 28, "icu_beds": 2, "icu_occupied": 0,
            "oxygen_available": True, "blood_bank": False,
            "diagnostics": ["CBC", "X-Ray", "Ultrasound", "Blood Sugar"],
            "specialists": ["Medicine", "Pediatrics"]
        },
        {
            "id": "fac-007", "facility_code": "AM-URULI-01",
            "name": "Arogya Mandir Uruli Kanchan", "type": FacilityType.AROGYA_MANDIR,
            "status": FacilityStatus.READY, "village": "Uruli Kanchan",
            "taluka": "Haveli", "lat": 18.4512, "lng": 74.0123,
            "phone": "020-27451239", "readiness_score": 88,
            "total_beds": 6, "occupied_beds": 1, "icu_beds": 0, "icu_occupied": 0,
            "oxygen_available": True, "blood_bank": False,
            "diagnostics": ["Blood Sugar", "Urine", "Hemoglobin"],
            "specialists": []
        },
        {
            "id": "fac-008", "facility_code": "AM-NANDED-01",
            "name": "Arogya Mandir Nanded Fata", "type": FacilityType.AROGYA_MANDIR,
            "status": FacilityStatus.READY, "village": "Nanded Fata",
            "taluka": "Haveli", "lat": 18.4678, "lng": 73.8456,
            "phone": "020-27451240", "readiness_score": 82,
            "total_beds": 4, "occupied_beds": 0, "icu_beds": 0, "icu_occupied": 0,
            "oxygen_available": True, "blood_bank": False,
            "diagnostics": ["Blood Sugar", "Hemoglobin"],
            "specialists": []
        },
        {
            "id": "fac-009", "facility_code": "DC-HADAPSAR-01",
            "name": "Diagnostic Centre Hadapsar", "type": FacilityType.DIAGNOSTIC_CENTRE,
            "status": FacilityStatus.READY, "village": "Hadapsar",
            "taluka": "Haveli", "lat": 18.5018, "lng": 73.9254,
            "phone": "020-27451241", "readiness_score": 95,
            "total_beds": 0, "occupied_beds": 0, "icu_beds": 0, "icu_occupied": 0,
            "oxygen_available": False, "blood_bank": False,
            "diagnostics": ["CBC", "X-Ray", "Ultrasound", "CT", "MRI", "Pathology"],
            "specialists": []
        },
        {
            "id": "fac-010", "facility_code": "BB-YERWADA-01",
            "name": "Blood Bank Yerwada", "type": FacilityType.BLOOD_BANK,
            "status": FacilityStatus.READY, "village": "Yerwada",
            "taluka": "Pune", "lat": 18.5523, "lng": 73.8901,
            "phone": "020-27451242", "readiness_score": 90,
            "total_beds": 0, "occupied_beds": 0, "icu_beds": 0, "icu_occupied": 0,
            "oxygen_available": False, "blood_bank": True,
            "diagnostics": [],
            "specialists": []
        },
    ]

    facilities = {}
    for fd in facilities_data:
        f = Facility(**fd)
        db.add(f)
        facilities[fd["id"]] = f

    db.flush()

    # ── Users ────────────────────────────────────────────────────────
    users_data = [
        {
            "id": "usr-001", "employee_id": "ASHA-HAV-001", "name": "Savita Mane",
            "email": "savita.mane@arogyamarg.gov.in", "phone": "9876543201",
            "role": RoleEnum.ASHA, "facility_id": "fac-007",
            "taluka": "Haveli", "village": "Uruli Kanchan",
            "password_hash": hash_password("demo1234")
        },
        {
            "id": "usr-002", "employee_id": "ASHA-HAV-002", "name": "Priya Shinde",
            "email": "priya.shinde@arogyamarg.gov.in", "phone": "9876543202",
            "role": RoleEnum.ASHA, "facility_id": "fac-008",
            "taluka": "Haveli", "village": "Nanded Fata",
            "password_hash": hash_password("demo1234")
        },
        {
            "id": "usr-003", "employee_id": "PHC-MAN-001", "name": "Dr. Anil Patil",
            "email": "anil.patil@arogyamarg.gov.in", "phone": "9876543203",
            "role": RoleEnum.PHC_DOCTOR, "facility_id": "fac-001",
            "taluka": "Haveli", "village": "Manjari",
            "password_hash": hash_password("demo1234")
        },
        {
            "id": "usr-004", "employee_id": "PHC-KES-001", "name": "Dr. Sunita Jadhav",
            "email": "sunita.jadhav@arogyamarg.gov.in", "phone": "9876543204",
            "role": RoleEnum.PHC_DOCTOR, "facility_id": "fac-002",
            "taluka": "Haveli", "village": "Kesnand",
            "password_hash": hash_password("demo1234")
        },
        {
            "id": "usr-005", "employee_id": "RH-WAG-001", "name": "Staff Ravi Kulkarni",
            "email": "ravi.kulkarni@arogyamarg.gov.in", "phone": "9876543205",
            "role": RoleEnum.HOSPITAL_STAFF, "facility_id": "fac-003",
            "taluka": "Haveli", "village": "Wagholi",
            "password_hash": hash_password("demo1234")
        },
        {
            "id": "usr-006", "employee_id": "DH-SAS-001", "name": "Dr. Meera Deshpande",
            "email": "meera.deshpande@arogyamarg.gov.in", "phone": "9876543206",
            "role": RoleEnum.SPECIALIST, "facility_id": "fac-005",
            "taluka": "Pune", "village": "Pune City",
            "password_hash": hash_password("demo1234")
        },
        {
            "id": "usr-007", "employee_id": "DA-PUNE-001", "name": "Dr. Rajesh Kale",
            "email": "rajesh.kale@arogyamarg.gov.in", "phone": "9876543207",
            "role": RoleEnum.DISTRICT_ADMIN, "facility_id": None,
            "taluka": "Pune", "village": "Pune City",
            "password_hash": hash_password("demo1234")
        },
        {
            "id": "usr-008", "employee_id": "HOSP-SAS-001", "name": "Staff Pooja Bhosale",
            "email": "pooja.bhosale@arogyamarg.gov.in", "phone": "9876543208",
            "role": RoleEnum.HOSPITAL_STAFF, "facility_id": "fac-005",
            "taluka": "Pune", "village": "Pune City",
            "password_hash": hash_password("demo1234")
        },
    ]

    users = {}
    for ud in users_data:
        u = User(**ud)
        db.add(u)
        users[ud["id"]] = u

    db.flush()

    # ── Ambulances ───────────────────────────────────────────────────
    ambulances_data = [
        {
            "id": "amb-001", "vehicle_number": "MH12-AB-1234", "vehicle_type": "BLS",
            "status": AmbulanceStatus.AVAILABLE, "base_facility_id": "fac-001",
            "driver_name": "Mahesh Pawar", "driver_phone": "9876501001",
            "current_lat": 18.5089, "current_lng": 73.9634
        },
        {
            "id": "amb-002", "vehicle_number": "MH12-AB-5678", "vehicle_type": "ALS",
            "status": AmbulanceStatus.DISPATCHED, "base_facility_id": "fac-003",
            "driver_name": "Sanjay More", "driver_phone": "9876501002",
            "current_lat": 18.5312, "current_lng": 73.9712,
            "destination_lat": 18.5565, "destination_lng": 73.9841,
            "eta_minutes": 12, "speed_kmph": 62.0
        },
        {
            "id": "amb-003", "vehicle_number": "MH12-CD-9012", "vehicle_type": "BLS",
            "status": AmbulanceStatus.AVAILABLE, "base_facility_id": "fac-005",
            "driver_name": "Ramesh Nimkar", "driver_phone": "9876501003",
            "current_lat": 18.5195, "current_lng": 73.8553
        },
    ]

    for ad in ambulances_data:
        db.add(Ambulance(**ad))

    db.flush()

    # ── Households ───────────────────────────────────────────────────
    households_data = [
        {
            "id": "hh-001", "household_code": "HH-URU-001",
            "address": "Survey No. 45, Near Temple, Uruli Kanchan",
            "village": "Uruli Kanchan", "taluka": "Haveli",
            "lat": 18.4523, "lng": 74.0134, "family_members_count": 4,
            "primary_contact_name": "Suresh Patil", "primary_contact_phone": "9876500001",
            "asha_id": "usr-001"
        },
        {
            "id": "hh-002", "household_code": "HH-URU-002",
            "address": "Plot No. 12, Main Road, Uruli Kanchan",
            "village": "Uruli Kanchan", "taluka": "Haveli",
            "lat": 18.4534, "lng": 74.0145, "family_members_count": 3,
            "primary_contact_name": "Ganesh Kamble", "primary_contact_phone": "9876500002",
            "asha_id": "usr-001"
        },
        {
            "id": "hh-003", "household_code": "HH-NAN-001",
            "address": "Behind School, Nanded Fata",
            "village": "Nanded Fata", "taluka": "Haveli",
            "lat": 18.4689, "lng": 73.8467, "family_members_count": 5,
            "primary_contact_name": "Vijay Shinde", "primary_contact_phone": "9876500003",
            "asha_id": "usr-002"
        },
    ]

    for hd in households_data:
        db.add(Household(**hd))

    db.flush()

    # ── Key Demo Patient: Rekha Patil ───────────────────────────────
    rekha = Patient(
        id="pat-rekha-001",
        patient_id="AM-PAT-2026-00428",
        care_id="CARE-2026-01872",
        name="Rekha Patil",
        age=28,
        gender=GenderEnum.FEMALE,
        phone="9876543100",
        village="Uruli Kanchan",
        district="Pune",
        household_id="hh-001",
        asha_id="usr-001",
        known_conditions=["Gestational Hypertension"],
        is_pregnant=True,
        trimester=3,
        medications=["Methyldopa 250mg"],
        allergies=[],
        prev_hospitalization=False,
        risk_level=RiskEnum.HIGH,
        risk_factors=["High BP", "Pregnancy", "Low Hemoglobin"],
        current_state=CarePathState.EN_ROUTE,
        current_facility_id="fac-003",
        consent_given=True,
        consent_date=datetime.utcnow() - timedelta(hours=3),
    )
    db.add(rekha)
    db.flush()

    # CarePath for Rekha
    rekha_cp = CarePath(
        id="cp-rekha-001",
        patient_id="pat-rekha-001",
        current_state=CarePathState.EN_ROUTE,
        next_best_action="Confirm arrival at Rural Hospital Wagholi and initiate maternal care protocol",
        responsible_user_id="usr-005",
        deadline=datetime.utcnow() + timedelta(minutes=25),
        is_active=True
    )
    db.add(rekha_cp)
    db.flush()

    cp_events = [
        CarePathEvent(id=gen_uuid(), carepath_id="cp-rekha-001",
                      from_state=None, to_state=CarePathState.IDENTIFIED,
                      event_type="PATIENT_IDENTIFIED", description="Patient identified during household visit",
                      performed_by="usr-001", created_at=datetime.utcnow() - timedelta(hours=4)),
        CarePathEvent(id=gen_uuid(), carepath_id="cp-rekha-001",
                      from_state=CarePathState.IDENTIFIED, to_state=CarePathState.TRIAGED,
                      event_type="TRIAGE_COMPLETED", description="High risk assessment: BP 150/95, Hb 9.2",
                      performed_by="usr-001", created_at=datetime.utcnow() - timedelta(hours=3, minutes=45)),
        CarePathEvent(id=gen_uuid(), carepath_id="cp-rekha-001",
                      from_state=CarePathState.TRIAGED, to_state=CarePathState.CONSULTATION_PENDING,
                      event_type="REFERRAL_TO_PHC", description="Referred to PHC Manjari for doctor consultation",
                      performed_by="usr-001", created_at=datetime.utcnow() - timedelta(hours=3, minutes=30)),
        CarePathEvent(id=gen_uuid(), carepath_id="cp-rekha-001",
                      from_state=CarePathState.CONSULTATION_PENDING, to_state=CarePathState.CONSULTED,
                      event_type="PHC_CONSULTATION", description="Dr. Anil Patil: Gestational HTN - requires hospital management",
                      performed_by="usr-003", created_at=datetime.utcnow() - timedelta(hours=2)),
        CarePathEvent(id=gen_uuid(), carepath_id="cp-rekha-001",
                      from_state=CarePathState.CONSULTED, to_state=CarePathState.REFERRAL_CREATED,
                      event_type="REFERRAL_CREATED", description="Referral to Rural Hospital Wagholi created",
                      performed_by="usr-003", created_at=datetime.utcnow() - timedelta(hours=1, minutes=45)),
        CarePathEvent(id=gen_uuid(), carepath_id="cp-rekha-001",
                      from_state=CarePathState.REFERRAL_CREATED, to_state=CarePathState.FACILITY_ACCEPTED,
                      event_type="REFERRAL_ACCEPTED", description="Rural Hospital Wagholi accepted referral",
                      performed_by="usr-005", created_at=datetime.utcnow() - timedelta(hours=1, minutes=20)),
        CarePathEvent(id=gen_uuid(), carepath_id="cp-rekha-001",
                      from_state=CarePathState.FACILITY_ACCEPTED, to_state=CarePathState.EN_ROUTE,
                      event_type="PATIENT_EN_ROUTE", description="Ambulance MH12-AB-1234 dispatched",
                      performed_by="usr-001", created_at=datetime.utcnow() - timedelta(minutes=30)),
    ]
    for ev in cp_events:
        db.add(ev)

    # Referral for Rekha
    rekha_ref = Referral(
        id="ref-rekha-001",
        referral_code="REF-2026-00891",
        patient_id="pat-rekha-001",
        origin_facility_id="fac-001",
        destination_facility_id="fac-003",
        referred_by="usr-003",
        status=ReferralStatus.EN_ROUTE,
        urgency=ReferralUrgency.URGENT,
        reason="Gestational Hypertension - Requires inpatient monitoring and management",
        clinical_notes="BP: 150/95 mmHg, Hb: 9.2 g/dL, 32 weeks gestation. Risk of pre-eclampsia.",
        required_specialty="Obstetrics",
        ambulance_id="amb-001",
        accepted_at=datetime.utcnow() - timedelta(hours=1, minutes=20),
        dispatched_at=datetime.utcnow() - timedelta(minutes=30),
        expected_arrival=datetime.utcnow() + timedelta(minutes=25),
    )
    db.add(rekha_ref)

    # ── Additional Patients ──────────────────────────────────────────
    additional_patients = [
        {
            "id": "pat-002", "patient_id": "AM-PAT-2026-00415", "care_id": "CARE-2026-01859",
            "name": "Anita Kamble", "age": 35, "gender": GenderEnum.FEMALE,
            "phone": "9876543101", "village": "Wagholi",
            "household_id": "hh-002", "asha_id": "usr-001",
            "known_conditions": ["Type 2 Diabetes", "Hypertension"],
            "risk_level": RiskEnum.HIGH, "risk_factors": ["Diabetes", "High BP", "Age"],
            "current_state": CarePathState.FOLLOW_UP_DUE,
            "consent_given": True, "consent_date": datetime.utcnow() - timedelta(days=15),
        },
        {
            "id": "pat-003", "patient_id": "AM-PAT-2026-00401", "care_id": "CARE-2026-01845",
            "name": "Ganesh Shinde", "age": 52, "gender": GenderEnum.MALE,
            "phone": "9876543102", "village": "Nanded Fata",
            "household_id": "hh-003", "asha_id": "usr-002",
            "known_conditions": ["COPD"],
            "risk_level": RiskEnum.MEDIUM, "risk_factors": ["Respiratory condition", "Age"],
            "current_state": CarePathState.TREATED,
            "consent_given": True, "consent_date": datetime.utcnow() - timedelta(days=10),
        },
        {
            "id": "pat-004", "patient_id": "AM-PAT-2026-00398", "care_id": "CARE-2026-01842",
            "name": "Sunita Jadhav", "age": 24, "gender": GenderEnum.FEMALE,
            "phone": "9876543103", "village": "Kesnand",
            "household_id": "hh-001", "asha_id": "usr-001",
            "known_conditions": [], "is_pregnant": True, "trimester": 2,
            "risk_level": RiskEnum.MEDIUM, "risk_factors": ["Pregnancy"],
            "current_state": CarePathState.CONSULTATION_PENDING,
            "consent_given": True, "consent_date": datetime.utcnow() - timedelta(days=2),
        },
        {
            "id": "pat-005", "patient_id": "AM-PAT-2026-00387", "care_id": "CARE-2026-01831",
            "name": "Ramesh Pawar", "age": 67, "gender": GenderEnum.MALE,
            "phone": "9876543104", "village": "Manjari",
            "household_id": "hh-002", "asha_id": "usr-001",
            "known_conditions": ["Heart Disease", "Hypertension"],
            "risk_level": RiskEnum.CRITICAL, "risk_factors": ["Cardiac", "High BP", "Elderly"],
            "current_state": CarePathState.REFERRAL_CREATED,
            "current_facility_id": "fac-001",
            "consent_given": True, "consent_date": datetime.utcnow() - timedelta(days=1),
        },
    ]

    for pd in additional_patients:
        p = Patient(**pd)
        db.add(p)
        db.flush()
        cp = CarePath(
            patient_id=pd["id"],
            current_state=pd["current_state"],
            next_best_action=_get_nba(pd["current_state"]),
            is_active=pd["current_state"] not in [CarePathState.CLOSED],
        )
        db.add(cp)

    # ── Tasks ────────────────────────────────────────────────────────
    tasks_data = [
        {
            "patient_id": "pat-rekha-001", "assigned_to": "usr-005",
            "title": "Confirm patient arrival and initiate maternal protocol",
            "task_type": "ARRIVAL_CONFIRM", "status": TaskStatus.OPEN,
            "priority": "HIGH", "due_at": datetime.utcnow() + timedelta(minutes=25),
            "related_referral_id": "ref-rekha-001"
        },
        {
            "patient_id": "pat-002", "assigned_to": "usr-001",
            "title": "Complete overdue follow-up for Anita Kamble",
            "task_type": "FOLLOW_UP", "status": TaskStatus.OPEN,
            "priority": "HIGH", "due_at": datetime.utcnow() - timedelta(hours=2),
        },
        {
            "patient_id": "pat-005", "assigned_to": "usr-003",
            "title": "Confirm referral acceptance for Ramesh Pawar",
            "task_type": "REFERRAL_CONFIRM", "status": TaskStatus.OPEN,
            "priority": "URGENT", "due_at": datetime.utcnow() + timedelta(minutes=15),
        },
    ]
    for td in tasks_data:
        db.add(CareTask(**td))

    # ── Simulation Scenarios ──────────────────────────────────────────
    scenarios = [
        {
            "name": "ICU Unavailable — Rural Hospital Wagholi",
            "description": "Simulate ICU going offline at Rural Hospital Wagholi",
            "scenario_type": "ICU_UNAVAILABLE",
            "target_facility_id": "fac-003",
            "config": {"icu_beds": 0, "icu_occupied": 0, "status": "LIMITED"},
            "is_active": False
        },
        {
            "name": "Oxygen Supply Failure — PHC Kesnand",
            "description": "Oxygen supply exhausted at PHC Kesnand",
            "scenario_type": "OXYGEN_UNAVAILABLE",
            "target_facility_id": "fac-002",
            "config": {"oxygen_available": False, "status": "CRITICAL"},
            "is_active": False
        },
        {
            "name": "Facility Overloaded — Sassoon District Hospital",
            "description": "All beds occupied at Sassoon",
            "scenario_type": "FACILITY_OVERLOADED",
            "target_facility_id": "fac-005",
            "config": {"occupied_beds": 250, "status": "CRITICAL"},
            "is_active": False
        },
    ]
    for sc in scenarios:
        db.add(SimulationScenario(**sc))

    db.commit()
    print("✅ Seed complete. Demo data loaded.")


def _get_nba(state: CarePathState) -> str:
    mapping = {
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
    return mapping.get(state, "Review patient status")
