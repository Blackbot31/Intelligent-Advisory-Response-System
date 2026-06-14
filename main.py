from subsystems.rnn import OutbreakTrendPredictor, MovementPatternRecognizer
from subsystems.rnn import OutbreakTrendPredictor
from fastapi.responses import Response
from pdf_generator import generate_report_pdf
from database.models import init_db
from database import crud
from orchestrator import IARMSOrchestrator
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import uvicorn

from subsystems.cce import CoordinationControlEngine
from subsystems.kau import KnowledgeAdvisoryUnit
from subsystems.cru import CommunicationResponseUnit
from subsystems.idru import IntelligentDistributionUnit
from subsystems.ceu import CollaborationEngagementUnit
from subsystems.srr import SecuredResourceRepository

# ─── Initialise App & Subsystems ─────────────────────────────────────────────
init_db()
app = FastAPI(
    title="IARMS - Intelligent Advisory and Response Management System",
    description="A framework for intelligent advisory and response "
                "management for infectious disease outbreaks",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

cce  = CoordinationControlEngine(state_size=10, action_size=4)
kau  = KnowledgeAdvisoryUnit()
cru  = CommunicationResponseUnit()
idru = IntelligentDistributionUnit()
ceu  = CollaborationEngagementUnit()
srr  = SecuredResourceRepository()
rnn  = OutbreakTrendPredictor()
orchestrator = IARMSOrchestrator(cce, kau, cru, idru, ceu, srr)

# ── Load persisted models if they exist ──────────────────────────────────────
cce_loaded = cce.load_model()
kau_loaded = kau.load_model()
print(f"CCE model loaded from disk: {cce_loaded}")
print(f"KAU model loaded from disk: {kau_loaded}")

# ── Load users from database into SRR ────────────────────────────────────────
stored_users = crud.load_all_users()
if stored_users:
    srr.users = stored_users
else:
    srr.register_user("admin_user", "SecurePass123", "admin")
    srr.register_user("field_officer", "FieldPass456", "officer")
    srr.register_user("analyst_user", "AnalystPass789", "analyst")
    for username, user_data in srr.users.items():
        crud.save_user(user_data)

# ─── Request Models ───────────────────────────────────────────────────────────
class OutbreakState(BaseModel):
    cases: float
    deaths: float
    resources: float
    hospitals: float
    personnel: float
    region_risk: float
    supply_level: float
    coordination_score: float
    days_since_outbreak: float
    response_level: float

class AdvisoryRequest(BaseModel):
    risk_score: float
    resource_level: float
    days_active: int
    cases: int
    deaths: int

class OutbreakData(BaseModel):
    disease: str
    region: str
    cases: int
    deaths: int
    fatality_rate: float
    spread_rate: float

class RegionData(BaseModel):
    region_id: str
    region_name: str
    population: int
    risk_score: float
    current_cases: int

class ResourceData(BaseModel):
    resource_type: str
    quantity: int
    source: str

class StakeholderData(BaseModel):
    name: str
    stakeholder_type: str
    region: str
    contact: str

class UserData(BaseModel):
    username: str
    password: str
    role: str

class LoginData(BaseModel):
    username: str
    password: str

class NLPCommand(BaseModel):
    command: str

class FeedbackData(BaseModel):
    stakeholder_id: str
    feedback_type: str
    message: str
    rating: float
    
class FullOutbreakInput(BaseModel):
    disease: str
    region: str
    cases: int
    deaths: int
    fatality_rate: float
    spread_rate: float
    risk_score: float
    resource_level: float
    days_active: int
    population: int
    coordination_score: float
    response_level: float
    neighbour_regions: dict = {}
    
class RNNRequest(BaseModel):
    case_history: list
    days_ahead: int = 3
    
class MovementRequest(BaseModel):
    region_data: dict
    days_ahead: int = 3

# ─── Root ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "system": "IARMS",
        "version": "1.0.0",
        "status": "Online",
        "subsystems": [
            "CCE - Coordination & Control Engine",
            "KAU - Knowledge-Based Advisory Unit",
            "CRU - Communication & Response Unit",
            "IDRU - Intelligent Distribution & Tracking Unit",
            "CEU - Collaboration & Engagement Unit",
            "SRR - Secured Resource Repository"
        ]
    }
    
from fastapi.responses import HTMLResponse

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("templates/dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ─── CCE Routes ───────────────────────────────────────────────────────────────
@app.post("/cce/recommend")
def cce_recommend(state: OutbreakState):
    state_list = [
        state.cases, state.deaths, state.resources,
        state.hospitals, state.personnel, state.region_risk,
        state.supply_level, state.coordination_score,
        state.days_since_outbreak, state.response_level
    ]
    return cce.get_recommendation(state_list)

# ─── KAU Routes ───────────────────────────────────────────────────────────────
@app.post("/kau/advisory")
def kau_advisory(request: AdvisoryRequest):
    state = request.dict()
    return kau.generate_advisory(state)

# ─── CRU Routes ───────────────────────────────────────────────────────────────
@app.post("/cru/response")
def cru_response(data: OutbreakData):
    return cru.generate_full_response(data.dict())

@app.post("/cru/hierarchy")
def cru_hierarchy(data: OutbreakData):
    result = cru.generate_full_response(data.dict())
    return result.get("coordination_hierarchy", {})

# ─── IDRU Routes ──────────────────────────────────────────────────────────────
@app.post("/idru/register-region")
def register_region(data: RegionData):
    idru.register_region(
        data.region_id, data.region_name,
        data.population, data.risk_score, data.current_cases
    )
    return {"success": True, "message": f"Region {data.region_name} registered"}

@app.post("/idru/add-resource")
def add_resource(data: ResourceData):
    resource_id = idru.add_resource(
        data.resource_type, data.quantity, data.source
    )
    return {"success": True, "resource_id": resource_id}

@app.get("/idru/tracking-report")
def tracking_report():
    return idru.get_tracking_report()

@app.get("/idru/visual-report")
def idru_visual_report():
    regions = []
    for rid, region in idru.regions.items():
        total_allocated = sum(region["resources_allocated"].values())
        coverage = min(100, round(
            (total_allocated / max(region["population"] * 0.01, 1)) * 100, 1
        ))
        risk_level = "HIGH" if region["risk_score"] > 0.6 else \
                     "MODERATE" if region["risk_score"] > 0.3 else "LOW"
        regions.append({
            "region_id":        rid,
            "name":             region["name"],
            "population":       region["population"],
            "risk_score":       region["risk_score"],
            "risk_level":       risk_level,
            "current_cases":    region["current_cases"],
            "total_allocated":  total_allocated,
            "coverage_percent": coverage,
            "last_updated":     region["last_updated"]
        })

    resources = []
    for rid, resource in idru.resource_registry.items():
        resources.append({
            "resource_id":      rid,
            "type":             resource["type"],
            "total_quantity":   resource["total_quantity"],
            "available":        resource["available_quantity"],
            "distributed":      resource["total_quantity"] - resource["available_quantity"],
            "status":           resource["status"],
            "source":           resource["source"]
        })

    return {
        "regions":             regions,
        "resources":           resources,
        "total_regions":       len(regions),
        "total_resources":     len(resources),
        "total_distributed":   sum(
            r["distributed"] for r in resources
        ),
        "undersupplied_regions": [
            r["name"] for r in regions
            if r["coverage_percent"] < 30
        ]
    }

# ─── CEU Routes ───────────────────────────────────────────────────────────────
@app.post("/ceu/register-stakeholder")
def register_stakeholder(data: StakeholderData):
    sid = ceu.register_stakeholder(
        data.name, data.stakeholder_type,
        data.region, data.contact
    )
    stakeholder_data = ceu.stakeholders[sid]
    crud.save_stakeholder(stakeholder_data)
    return {"success": True, "stakeholder_id": sid}

@app.post("/ceu/feedback")
def submit_feedback(data: FeedbackData):
    return ceu.submit_feedback(
        data.stakeholder_id, data.feedback_type,
        data.message, data.rating
    )

@app.get("/ceu/engagement-summary")
def engagement_summary():
    return ceu.get_engagement_summary()

# ─── SRR Routes ───────────────────────────────────────────────────────────────
@app.post("/srr/register")
def register_user(data: UserData):
    result = srr.register_user(data.username, data.password, data.role)
    if "error" not in result:
        user_data = srr.users[data.username]
        crud.save_user(user_data)
    return result

@app.post("/srr/login")
def login(data: LoginData):
    result = srr.login(data.username, data.password)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@app.post("/srr/command")
def nlp_command(data: NLPCommand,
                authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401,
                            detail="Session token required")
    return srr.process_nlp_command(authorization, data.command)

@app.post("/outbreak/analyse")
def full_analysis(data: FullOutbreakInput,
                  authorization: Optional[str] = Header(None)):
    result = orchestrator.run_full_analysis(
        data.dict(),
        srr_token=authorization
    )
    crud.save_outbreak_report(result, data.dict())
    allocations = result["idru"].get("allocations", [])
    if isinstance(allocations, list) and allocations:
        crud.save_allocations(allocations, result["report_id"])
    return result

@app.get("/reports/history")
def reports_history():
    return crud.load_all_reports()

@app.get("/reports/history/{report_id}")
def get_report(report_id: str):
    db_reports = crud.load_all_reports()
    for r in db_reports:
        if r["report_id"] == report_id:
            allocations = crud.load_allocations_by_report(report_id)
            r["allocations"] = allocations
            return r
    raise HTTPException(status_code=404, detail="Report not found")

@app.get("/reports/export/{report_id}")
def export_report_pdf(report_id: str):
    db_reports = crud.load_all_reports()
    report = None
    for r in db_reports:
        if r["report_id"] == report_id:
            report = r
            break
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    allocations = crud.load_allocations_by_report(report_id)
    report["allocations"] = allocations
    pdf_bytes = generate_report_pdf(report)
    timestamp = report.get("timestamp", "").replace(":", "-").replace(" ", "_")
    filename = f"IARMS_Report_{report_id}_{timestamp}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
@app.post("/rnn/predict")
def rnn_predict(data: RNNRequest):
    predictor = OutbreakTrendPredictor()
    result = predictor.run_full_analysis(data.case_history, data.days_ahead)
    return result

@app.post("/rnn/movement")
def rnn_movement(data: MovementRequest):
    recognizer = MovementPatternRecognizer()
    result = recognizer.analyze(data.region_data, data.days_ahead)
    return result

@app.get("/models/status")
def model_status():
    import os
    cce_exists = os.path.exists("models/cce_model.pt")
    kau_exists = os.path.exists("models/kau_qtable.json")
    cce_size   = round(
        os.path.getsize("models/cce_model.pt") / 1024, 2
    ) if cce_exists else 0
    kau_size   = round(
        os.path.getsize("models/kau_qtable.json") / 1024, 2
    ) if kau_exists else 0
    return {
        "cce": {
            "saved":      cce_exists,
            "file_size":  f"{cce_size} KB",
            "epsilon":    round(cce.epsilon, 4),
            "confidence": round((1 - cce.epsilon) * 100, 2),
            "memory_size": len(cce.memory)
        },
        "kau": {
            "saved":        kau_exists,
            "file_size":    f"{kau_size} KB",
            "epsilon":      round(kau.epsilon, 4),
            "states_learned": len(kau.q_table)
        }
    }

# ─── Run Server ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)