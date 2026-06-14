from database.models import (
    SessionLocal, User, OutbreakReport,
    ResourceAllocation, Stakeholder,
    EngagementLog, AccessLog, InterventionOutcome
)

from database.models import (
    SessionLocal, User, OutbreakReport,
    ResourceAllocation, Stakeholder,
    EngagementLog, AccessLog
)


def get_session():
    return SessionLocal()


# ── USERS ──────────────────────────────────────────────────────────────────
def save_user(user_data: dict):
    db = get_session()
    try:
        existing = db.query(User).filter(
            User.username == user_data["username"]
        ).first()
        if existing:
            return False
        user = User(
            username=user_data["username"],
            user_id=user_data["user_id"],
            password_hash=user_data["password_hash"],
            role=user_data["role"],
            permissions=",".join(user_data["permissions"]),
            date_registered=user_data["date_registered"]
        )
        db.add(user)
        db.commit()
        return True
    finally:
        db.close()


def load_all_users():
    db = get_session()
    try:
        users = db.query(User).all()
        result = {}
        for u in users:
            result[u.username] = {
                "user_id": u.user_id,
                "username": u.username,
                "password_hash": u.password_hash,
                "role": u.role,
                "permissions": u.permissions.split(","),
                "date_registered": u.date_registered
            }
        return result
    finally:
        db.close()


# ── OUTBREAK REPORTS ────────────────────────────────────────────────────────
def save_outbreak_report(report: dict, input_data: dict):
    db = get_session()
    try:
        record = OutbreakReport(
            report_id=report["report_id"],
            timestamp=report["timestamp"],
            disease=report["disease"],
            region=report["region"],
            severity=report["severity"],
            cases=input_data.get("cases", 0),
            deaths=input_data.get("deaths", 0),
            fatality_rate=input_data.get("fatality_rate", 0),
            spread_rate=input_data.get("spread_rate", 0),
            risk_score=input_data.get("risk_score", 0),
            resource_level=input_data.get("resource_level", 0),
            days_active=input_data.get("days_active", 0),
            cce_recommendation=report["cce"]["recommendation"],
            kau_stage=report["kau"]["outbreak_stage"],
            kau_advisory=report["kau"]["primary_advisory"],
            cru_severity=report["cru"]["severity"],
            resources_allocated=report["idru"]["resources_allocated"],
            stakeholders_engaged=report["ceu"]["stakeholders_engaged"],
            written_report=report.get("written_report", "")
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def load_all_reports():
    db = get_session()
    try:
        reports = db.query(OutbreakReport).order_by(
            OutbreakReport.timestamp.desc()
        ).all()
        return [
            {
                "report_id": r.report_id,
                "timestamp": r.timestamp,
                "disease": r.disease,
                "region": r.region,
                "severity": r.severity,
                "cases": r.cases,
                "deaths": r.deaths,
                "fatality_rate": r.fatality_rate,
                "spread_rate": r.spread_rate,
                "risk_score": r.risk_score,
                "resource_level": r.resource_level,
                "days_active": r.days_active,
                "cce_recommendation": r.cce_recommendation,
                "kau_stage": r.kau_stage,
                "kau_advisory": r.kau_advisory,
                "cru_severity": r.cru_severity,
                "resources_allocated": r.resources_allocated,
                "stakeholders_engaged": r.stakeholders_engaged,
                "written_report": r.written_report
            }
            for r in reports
        ]
    finally:
        db.close()


# ── RESOURCE ALLOCATIONS ────────────────────────────────────────────────────
def save_allocations(allocations: list, report_id: str):
    db = get_session()
    try:
        for alloc in allocations:
            record = ResourceAllocation(
                tracking_id=alloc["tracking_id"],
                report_id=report_id,
                resource_type=alloc["resource_type"],
                region_name=alloc["region_name"],
                quantity_allocated=alloc["quantity_allocated"],
                priority_score=alloc["priority_score"],
                status=alloc["status"],
                timestamp=alloc["timestamp"]
            )
            db.add(record)
        db.commit()
    finally:
        db.close()


# ── STAKEHOLDERS ────────────────────────────────────────────────────────────
def save_stakeholder(stakeholder: dict):
    db = get_session()
    try:
        existing = db.query(Stakeholder).filter(
            Stakeholder.stakeholder_id == stakeholder["stakeholder_id"]
        ).first()
        if existing:
            return
        record = Stakeholder(
            stakeholder_id=stakeholder["stakeholder_id"],
            name=stakeholder["name"],
            type=stakeholder["type"],
            region=stakeholder["region"],
            contact=stakeholder["contact"],
            status=stakeholder["status"],
            date_registered=stakeholder["date_registered"]
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def load_all_stakeholders():
    db = get_session()
    try:
        stakeholders = db.query(Stakeholder).all()
        return [
            {
                "stakeholder_id": s.stakeholder_id,
                "name": s.name,
                "type": s.type,
                "region": s.region,
                "contact": s.contact,
                "status": s.status,
                "date_registered": s.date_registered
            }
            for s in stakeholders
        ]
    finally:
        db.close()


# ── ENGAGEMENT LOGS ─────────────────────────────────────────────────────────
def save_engagement(engagement: dict):
    db = get_session()
    try:
        record = EngagementLog(
            engagement_id=engagement["engagement_id"],
            stakeholder_id=engagement["stakeholder_id"],
            stakeholder_name=engagement["stakeholder_name"],
            channel=engagement["channel"],
            summary=engagement["summary"],
            timestamp=engagement["timestamp"]
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


# ── ACCESS LOGS ─────────────────────────────────────────────────────────────
def save_access_log(log: dict):
    db = get_session()
    try:
        record = AccessLog(
            log_id=log["log_id"],
            username=log["username"],
            action=log["action"],
            resource_id=log["resource_id"],
            note=log["note"],
            timestamp=log["timestamp"]
        )
        db.add(record)
        db.commit()
    finally:
        db.close()
        
def load_allocations_by_report(report_id: str):
    db = get_session()
    try:
        allocations = db.query(ResourceAllocation).filter(
            ResourceAllocation.report_id == report_id
        ).all()
        return [
            {
                "tracking_id": a.tracking_id,
                "resource_type": a.resource_type,
                "region_name": a.region_name,
                "quantity_allocated": a.quantity_allocated,
                "priority_score": a.priority_score,
                "status": a.status,
                "timestamp": a.timestamp
            }
            for a in allocations
        ]
    finally:
        db.close()
        
def save_outcome(outcome: dict):
    db = get_session()
    try:
        record = InterventionOutcome(
            outcome_id          = outcome["outcome_id"],
            report_id           = outcome["report_id"],
            disease             = outcome["disease"],
            region              = outcome["region"],
            cce_recommendation  = outcome["cce_recommendation"],
            cases_before        = outcome["cases_before"],
            cases_after         = outcome["cases_after"],
            deaths_before       = outcome["deaths_before"],
            deaths_after        = outcome["deaths_after"],
            outcome_rating      = outcome["outcome_rating"],
            effectiveness_score = outcome["effectiveness_score"],
            notes               = outcome["notes"],
            recorded_by         = outcome["recorded_by"],
            timestamp           = outcome["timestamp"]
        )
        db.add(record)
        db.commit()
        return True
    finally:
        db.close()


def load_all_outcomes():
    db = get_session()
    try:
        outcomes = db.query(InterventionOutcome).order_by(
            InterventionOutcome.timestamp.desc()
        ).all()
        return [
            {
                "outcome_id":          o.outcome_id,
                "report_id":           o.report_id,
                "disease":             o.disease,
                "region":              o.region,
                "cce_recommendation":  o.cce_recommendation,
                "cases_before":        o.cases_before,
                "cases_after":         o.cases_after,
                "deaths_before":       o.deaths_before,
                "deaths_after":        o.deaths_after,
                "outcome_rating":      o.outcome_rating,
                "effectiveness_score": o.effectiveness_score,
                "notes":               o.notes,
                "recorded_by":         o.recorded_by,
                "timestamp":           o.timestamp
            }
            for o in outcomes
        ]
    finally:
        db.close()