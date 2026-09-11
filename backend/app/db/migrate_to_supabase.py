"""
Migration Script: Transfer local SQLite database data (arogya_marg_demo.db) to Supabase PostgreSQL.
"""
import sys
import os
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings
from app.db.database import Base
from app.models.models import (
    User, Facility, Patient, Household, CarePath, CarePathEvent,
    Referral, FollowUp, CareTask, Notification, AuditEvent, Ambulance,
    SimulationScenario, Observation, Encounter
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLITE_URL = "sqlite:///./arogya_marg_demo.db"


def migrate():
    target_url = settings.DATABASE_URL
    if target_url.startswith("sqlite"):
        logger.error("DATABASE_URL in .env is currently set to SQLite. Please update DATABASE_URL to your Supabase PostgreSQL URI.")
        sys.exit(1)

    logger.info("Connecting to local SQLite database: %s", SQLITE_URL)
    sqlite_engine = create_engine(SQLITE_URL)
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_db = SQLiteSession()

    logger.info("Connecting to Supabase PostgreSQL database...")
    pg_engine = create_engine(target_url, pool_pre_ping=True)
    PgSession = sessionmaker(bind=pg_engine)
    pg_db = PgSession()

    logger.info("Step 1: Creating database schema on Supabase...")
    Base.metadata.create_all(bind=pg_engine)
    logger.info("✅ PostgreSQL tables created/verified successfully!")

    models_in_order = [
        ("Facilities", Facility),
        ("Users", User),
        ("Households", Household),
        ("Patients", Patient),
        ("Care Paths", CarePath),
        ("Encounters", Encounter),
        ("CarePath Events", CarePathEvent),
        ("Referrals", Referral),
        ("Follow-ups", FollowUp),
        ("Care Tasks", CareTask),
        ("Notifications", Notification),
        ("Audit Events", AuditEvent),
        ("Ambulances", Ambulance),
        ("Simulation Scenarios", SimulationScenario),
        ("Observations", Observation),
    ]

    logger.info("Step 2: Migrating data table by table...")

    for name, model in models_in_order:
        try:
            records = sqlite_db.query(model).all()
            if not records:
                logger.info("  -> Table '%s': 0 records (Skipping)", name)
                continue

            count = 0
            for obj in records:
                # Merge or add object state to PG session
                dict_data = {c.name: getattr(obj, c.name) for c in inspect(obj).mapper.column_attrs}
                new_obj = model(**dict_data)
                pg_db.merge(new_obj)
                count += 1

            pg_db.commit()
            logger.info("  -> Table '%s': Transferred %d records successfully!", name, count)
        except Exception as e:
            pg_db.rollback()
            logger.error("  ❌ Error migrating table '%s': %s", name, str(e))

    sqlite_db.close()
    pg_db.close()
    logger.info("🎉 Migration to Supabase PostgreSQL completed successfully!")


if __name__ == "__main__":
    migrate()
