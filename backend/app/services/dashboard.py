from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import Execution, Model, Request, Response

def overview(db: Session):
    total = db.query(func.count(Request.id)).scalar() or 0
    cost = db.query(func.coalesce(func.sum(Response.total_cost), 0)).scalar() or 0
    latency = db.query(func.avg(Response.total_latency)).scalar() or 0
    quality = db.query(func.avg(Response.final_quality_score)).scalar() or 0
    escalated = db.query(func.count(Response.id)).filter(Response.escalated.is_(True)).scalar() or 0
    overrides = 0
    return {"total_requests": total, "total_cost": round(cost, 6), "average_cost": round(cost/total, 6) if total else 0, "average_latency": round(latency, 3), "average_quality": round(quality, 3), "escalation_rate": round(escalated/total, 3) if total else 0, "override_rate": overrides, "estimated_cost_saved": None, "note": "Savings require a completed baseline experiment."}

def model_stats(db: Session):
    rows = db.query(Model.name, Model.type, func.count(Execution.id), func.sum(Execution.estimated_cost), func.avg(Execution.latency), func.avg(Execution.quality_score)).join(Execution, Model.id == Execution.model_id, isouter=True).group_by(Model.id).all()
    return [{"model": n, "type": model_type, "requests": int(request_count or 0), "cost": round(float(cost or 0), 6), "latency": round(float(lat or 0), 3), "quality": round(float(q or 0), 3)} for n,model_type,request_count,cost,lat,q in rows]
