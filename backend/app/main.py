import asyncio
import json
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import EvaluationResult, EvaluationRun, Execution, Model, Request, Response, RoutingDecision, Task
from .schemas import ChatRequest, EvaluationRequest, ModelUpdate, RouteRequest
from .services.analysis import analyze, decompose
from .services.dashboard import model_stats, overview
from .services.execution import execute
from .services.quality import evaluate
from .services.registry import candidates
from .services.routing import route

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Intelligent LLM Router", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
async def health(db: Session = Depends(get_db)):
    items = await candidates(db)
    return {"backend":"ONLINE", "database":"CONNECTED", "providers":[{"provider": c.provider, "model": c.identifier, "available": c.available, "local": c.local} for c in items]}

@app.get("/api/models")
async def models(db: Session = Depends(get_db)):
    await candidates(db)
    return [{"id":m.id,"name":m.name,"provider":m.provider,"model_identifier":m.model_identifier,"type":m.type,"capability":m.capability,"cost_input":m.cost_input,"cost_output":m.cost_output,"context_limit":m.context_limit,"is_local":m.is_local,"is_active":m.is_active} for m in db.query(Model).all()]

@app.patch("/api/models/{model_id}")
def update_model(model_id: int, update: ModelUpdate, db: Session = Depends(get_db)):
    model = db.get(Model, model_id)
    if not model: raise HTTPException(404, "Model not found")
    for key, value in update.model_dump(exclude_none=True).items(): setattr(model, key, value)
    db.commit(); return {"ok": True}

@app.post("/api/route")
async def route_request(payload: RouteRequest, db: Session = Depends(get_db)):
    analysis = analyze(payload.prompt, payload.privacy_level)
    try:
        decision = route(analysis, await candidates(db), payload.mode, payload.optimization_preference)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"analysis": analysis.__dict__, "selected_model": decision.selected.identifier, "routing_score": decision.score, "routing_reason": decision.reason, "alternative_models": decision.alternatives}

@app.post("/api/chat")
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    analysis = analyze(payload.prompt, payload.privacy_level)
    request = Request(request_text=payload.prompt, complexity=analysis.complexity, task_type=analysis.task_type, privacy_level=analysis.privacy); db.add(request); db.flush()
    available = await candidates(db); results=[]; quality_scores=[]; total_cost=0; total_latency=0; escalated=False; selected_names=[]
    parts = decompose(payload.prompt)
    for number, part in enumerate(parts, 1):
        part_analysis = analyze(part, payload.privacy_level)
        try: decision = route(part_analysis, available, payload.mode, payload.optimization_preference)
        except RuntimeError as exc: raise HTTPException(503, str(exc))
        task = Task(request_id=request.id, task_number=number, description=part, task_type=part_analysis.task_type, complexity=part_analysis.complexity, routing_score=decision.score, routing_reason=decision.reason); db.add(task); db.flush()
        db.add(RoutingDecision(request_id=request.id, selected_model=decision.selected.identifier, reason=decision.reason, score=decision.score, user_override=payload.mode != "AUTO", override_model=decision.selected.identifier if payload.mode != "AUTO" else None))
        candidates_to_try = [decision.selected] + [next((c for c in available if c.identifier == a["model"]), None) for a in decision.alternatives]
        answer = None; quality = None
        for attempt, candidate in enumerate([c for c in candidates_to_try if c], 1):
            try:
                generation = await execute(candidate.identifier, part)
                quality = evaluate(part, generation.text)
                if quality.quality_score >= settings.quality_threshold or attempt > settings.max_escalations: answer = generation; escalated = escalated or attempt > 1; break
            except Exception:
                if attempt > settings.max_escalations: break
        if not answer:
            db.rollback()
            raise HTTPException(503, "All configured providers failed. Start LM Studio or configure a cloud API key.")
        model = db.query(Model).filter_by(model_identifier=candidate.identifier).first()
        cost = candidate.cost_input * answer.input_tokens + candidate.cost_output * answer.output_tokens
        db.add(Execution(task_id=task.id, model_id=model.id, input_tokens=answer.input_tokens, output_tokens=answer.output_tokens, estimated_cost=cost, actual_cost=cost, latency=answer.latency, quality_score=quality.quality_score, confidence_score=quality.confidence_score, success=True, response_text=answer.text))
        results.append(f"### Part {number}\n{answer.text}"); quality_scores.append(quality.quality_score); total_cost += cost; total_latency += answer.latency; selected_names.append(candidate.identifier)
    final = "\n\n".join(results); avg_quality = sum(quality_scores) / len(quality_scores)
    db.add(Response(request_id=request.id, final_response=final, total_cost=total_cost, total_latency=total_latency, final_quality_score=avg_quality, confidence_score=min(1, avg_quality+.08), escalated=escalated)); db.commit()
    return {"request_id":request.id,"final_response":final,"selected_models":selected_names,"analysis":analysis.__dict__,"total_cost":total_cost,"total_latency":total_latency,"quality_score":avg_quality,"confidence_score":min(1,avg_quality+.08),"escalated":escalated,"override":payload.mode != "AUTO"}

@app.get("/api/requests")
def requests(db: Session = Depends(get_db)):
    completed = db.query(Request).filter(Request.response.has()).order_by(Request.id.desc()).limit(100).all()
    return [{"id":r.id,"request":r.request_text,"created_at":r.created_at,"complexity":r.complexity,"task_type":r.task_type,"privacy_level":r.privacy_level,"response":r.response.final_response,"cost":r.response.total_cost,"latency":r.response.total_latency,"quality":r.response.final_quality_score} for r in completed]

@app.get("/api/requests/{request_id}")
def request_detail(request_id: int, db: Session = Depends(get_db)):
    r=db.get(Request, request_id)
    if not r: raise HTTPException(404, "Request not found")
    return {"id":r.id,"request":r.request_text,"analysis":{"complexity":r.complexity,"task_type":r.task_type,"privacy_level":r.privacy_level},"tasks":[{"description":t.description,"model":t.model.model_identifier if t.model else None,"score":t.routing_score,"reason":t.routing_reason,"executions":[{"latency":e.latency,"cost":e.estimated_cost,"quality":e.quality_score,"success":e.success} for e in t.executions]} for t in r.tasks],"response":r.response.final_response if r.response else None}

@app.get("/api/dashboard/overview")
def dashboard_overview(db: Session = Depends(get_db)): return overview(db)
@app.get("/api/dashboard/models")
def dashboard_models(db: Session = Depends(get_db)): return model_stats(db)
@app.get("/api/dashboard/cost")
def dashboard_cost(db: Session = Depends(get_db)): return model_stats(db)
@app.get("/api/dashboard/latency")
def dashboard_latency(db: Session = Depends(get_db)): return model_stats(db)
@app.get("/api/dashboard/quality")
def dashboard_quality(db: Session = Depends(get_db)): return model_stats(db)

@app.post("/api/evaluate")
async def evaluate_dataset(payload: EvaluationRequest, db: Session = Depends(get_db)):
    dataset_path = Path(__file__).resolve().parents[2] / "data" / "evaluation_dataset.json"
    items = json.loads(dataset_path.read_text(encoding="utf-8"))[:payload.limit]
    available = await candidates(db)
    usable = [c for c in available if c.available]
    if not usable:
        raise HTTPException(503, "Evaluation needs at least one available provider. Start LM Studio or configure a cloud API key.")
    baseline_model = next((candidate for candidate in usable if candidate.type == "STRONG"), None)
    if not baseline_model:
        raise HTTPException(503, "Baseline requires an available STRONG model")
    baseline = {"cost": 0.0, "latency": 0.0, "quality": [], "strong_requests": 0, "successful": 0, "failed": 0, "usage": {"LOCAL": 0, "MEDIUM": 0, "STRONG": 0}}
    routed = {"cost": 0.0, "latency": 0.0, "quality": [], "strong_requests": 0, "successful": 0, "failed": 0, "usage": {"LOCAL": 0, "MEDIUM": 0, "STRONG": 0}}
    run = EvaluationRun(run_type="COMPARISON", dataset_name="evaluation_dataset.json", total_questions=len(items)); db.add(run); db.flush()
    for item in items:
        prompt = item["question"]
        try:
            baseline_generation = await execute(baseline_model.identifier, prompt)
            baseline_quality = evaluate(prompt, baseline_generation.text)
            baseline_cost = baseline_model.cost_input * baseline_generation.input_tokens + baseline_model.cost_output * baseline_generation.output_tokens
            baseline["cost"] += baseline_cost; baseline["latency"] += baseline_generation.latency; baseline["quality"].append(baseline_quality.quality_score); baseline["strong_requests"] += 1; baseline["successful"] += 1; baseline["usage"][baseline_model.type] += 1
            db.add(EvaluationResult(run_id=run.id, run_type="BASELINE", question_id=str(item["id"]), category=item["category"], selected_model=baseline_model.identifier, cost=baseline_cost, latency=baseline_generation.latency, quality=baseline_quality.quality_score, correctness=baseline_quality.quality_score, relevance=baseline_quality.quality_score, completeness=baseline_quality.quality_score, clarity=baseline_quality.quality_score, success=True))
        except Exception:
            baseline["failed"] += 1
        analysis = analyze(prompt)
        decision = route(analysis, available, preference="BALANCED")
        try:
            routed_generation = await execute(decision.selected.identifier, prompt)
            routed_quality = evaluate(prompt, routed_generation.text)
            routed_cost = decision.selected.cost_input * routed_generation.input_tokens + decision.selected.cost_output * routed_generation.output_tokens
            routed["cost"] += routed_cost; routed["latency"] += routed_generation.latency; routed["quality"].append(routed_quality.quality_score); routed["strong_requests"] += int(decision.selected.capability == baseline_model.capability); routed["successful"] += 1; routed["usage"][decision.selected.type] += 1
            db.add(EvaluationResult(run_id=run.id, run_type="ROUTER", question_id=str(item["id"]), category=item["category"], selected_model=decision.selected.identifier, cost=routed_cost, latency=routed_generation.latency, quality=routed_quality.quality_score, correctness=routed_quality.quality_score, relevance=routed_quality.quality_score, completeness=routed_quality.quality_score, clarity=routed_quality.quality_score, success=True))
        except Exception:
            routed["failed"] += 1
    count = max(1, len(items))
    baseline_quality = sum(baseline["quality"]) / max(1, len(baseline["quality"]))
    routed_quality = sum(routed["quality"]) / max(1, len(routed["quality"]))
    savings = baseline["cost"] - routed["cost"]
    run.total_cost = baseline["cost"] + routed["cost"]; run.average_cost = run.total_cost / max(1, count); run.average_latency = (baseline["latency"] + routed["latency"]) / max(1, count * 2); run.average_quality = (baseline_quality + routed_quality) / 2; db.commit()
    def summary(data, quality):
        return {"total_cost": data["cost"], "average_cost": data["cost"] / count, "average_latency": data["latency"] / count, "average_quality": quality, "strong_model_usage": data["strong_requests"] / count, "model_usage": {k: v / count for k, v in data["usage"].items()}, "successful_requests": data["successful"], "failed_requests": data["failed"]}
    return {"items": len(items), "baseline": summary(baseline, baseline_quality), "router": summary(routed, routed_quality), "cost_savings": savings, "savings_percent": savings / baseline["cost"] * 100 if baseline["cost"] else None}

@app.get("/api/evaluations/latest")
def latest_evaluation(db: Session = Depends(get_db)):
    run = db.query(EvaluationRun).order_by(EvaluationRun.id.desc()).first()
    if not run: return None
    rows = db.query(EvaluationResult).filter_by(run_id=run.id).all()
    return {"run_id": run.id, "dataset_name": run.dataset_name, "total_questions": run.total_questions, "results": [{"run_type": r.run_type, "model": r.selected_model, "cost": r.cost, "latency": r.latency, "quality": r.quality, "category": r.category} for r in rows]}
