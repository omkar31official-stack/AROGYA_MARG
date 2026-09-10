from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base, SessionLocal
from app.api.routes import auth, patients, referrals, facilities, network, analytics, simulation, tasks
from app.db.seed import seed_database

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Arogya Marga API",
    description="Patient Journey Orchestration & Public-Health Coordination Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "Arogya Marg API", "version": "1.0.0"}


# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(referrals.router, prefix="/referrals", tags=["referrals"])
app.include_router(facilities.router, prefix="/facilities", tags=["facilities"])
app.include_router(network.router, prefix="/network", tags=["network"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
app.include_router(tasks.router, prefix="/ops", tags=["tasks"])
