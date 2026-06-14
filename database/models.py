from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./iarms.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    username         = Column(String, primary_key=True, index=True)
    user_id          = Column(String, unique=True)
    password_hash    = Column(String)
    role             = Column(String)
    permissions      = Column(String)
    date_registered  = Column(String)


class OutbreakReport(Base):
    __tablename__ = "outbreak_reports"
    report_id        = Column(String, primary_key=True)
    timestamp        = Column(String)
    disease          = Column(String)
    region           = Column(String)
    severity         = Column(String)
    cases            = Column(Integer)
    deaths           = Column(Integer)
    fatality_rate    = Column(Float)
    spread_rate      = Column(Float)
    risk_score       = Column(Float)
    resource_level   = Column(Float)
    days_active      = Column(Integer)
    cce_recommendation = Column(String)
    kau_stage        = Column(String)
    kau_advisory     = Column(String)
    cru_severity     = Column(String)
    resources_allocated = Column(Integer)
    stakeholders_engaged = Column(Integer)
    written_report   = Column(Text)


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"
    tracking_id      = Column(String, primary_key=True)
    report_id        = Column(String)
    resource_type    = Column(String)
    region_name      = Column(String)
    quantity_allocated = Column(Integer)
    priority_score   = Column(Float)
    status           = Column(String)
    timestamp        = Column(String)


class Stakeholder(Base):
    __tablename__ = "stakeholders"
    stakeholder_id   = Column(String, primary_key=True)
    name             = Column(String)
    type             = Column(String)
    region           = Column(String)
    contact          = Column(String)
    status           = Column(String)
    date_registered  = Column(String)


class EngagementLog(Base):
    __tablename__ = "engagement_logs"
    engagement_id    = Column(String, primary_key=True)
    stakeholder_id   = Column(String)
    stakeholder_name = Column(String)
    channel          = Column(String)
    summary          = Column(Text)
    timestamp        = Column(String)


class AccessLog(Base):
    __tablename__ = "access_logs"
    log_id           = Column(String, primary_key=True)
    username         = Column(String)
    action           = Column(String)
    resource_id      = Column(String)
    note             = Column(String)
    timestamp        = Column(String)
    
class InterventionOutcome(Base):
    __tablename__ = "intervention_outcomes"
    outcome_id          = Column(String, primary_key=True)
    report_id           = Column(String)
    disease             = Column(String)
    region              = Column(String)
    cce_recommendation  = Column(String)
    cases_before        = Column(Integer)
    cases_after         = Column(Integer)
    deaths_before       = Column(Integer)
    deaths_after        = Column(Integer)
    outcome_rating      = Column(String)
    effectiveness_score = Column(Float)
    notes               = Column(Text)
    recorded_by         = Column(String)
    timestamp           = Column(String)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()