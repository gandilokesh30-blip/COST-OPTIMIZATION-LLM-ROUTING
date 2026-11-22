from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now(): return datetime.now(timezone.utc)

class Model(Base):
    __tablename__ = "models"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(40))
    model_identifier: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[str] = mapped_column(String(20))
    capability: Mapped[int] = mapped_column(Integer, default=1)
    cost_input: Mapped[float] = mapped_column(Float, default=0)
    cost_output: Mapped[float] = mapped_column(Float, default=0)
    context_limit: Mapped[int] = mapped_column(Integer, default=8192)
    is_local: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Request(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_text: Mapped[str] = mapped_column(Text)
    complexity: Mapped[str] = mapped_column(String(20))
    task_type: Mapped[str] = mapped_column(String(40))
    privacy_level: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    tasks: Mapped[list["Task"]] = relationship(cascade="all, delete-orphan")
    response: Mapped["Response"] = relationship(cascade="all, delete-orphan", uselist=False)

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    task_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(40))
    complexity: Mapped[str] = mapped_column(String(20))
    selected_model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=True)
    routing_score: Mapped[float] = mapped_column(Float, default=0)
    routing_reason: Mapped[str] = mapped_column(Text, default="")
    executions: Mapped[list["Execution"]] = relationship(cascade="all, delete-orphan")
    model: Mapped["Model"] = relationship()

class Execution(Base):
    __tablename__ = "model_executions"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    actual_cost: Mapped[float] = mapped_column(Float, nullable=True)
    latency: Mapped[float] = mapped_column(Float, default=0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    response_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class RoutingDecision(Base):
    __tablename__ = "routing_decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    selected_model: Mapped[str] = mapped_column(String(120))
    reason: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    user_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_model: Mapped[str] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class Response(Base):
    __tablename__ = "responses"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    final_response: Mapped[str] = mapped_column(Text)
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    total_latency: Mapped[float] = mapped_column(Float, default=0)
    final_quality_score: Mapped[float] = mapped_column(Float, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_type: Mapped[str] = mapped_column(String(30), default="COMPARISON")
    dataset_name: Mapped[str] = mapped_column(String(120))
    total_questions: Mapped[int] = mapped_column(Integer)
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    average_cost: Mapped[float] = mapped_column(Float, default=0)
    average_latency: Mapped[float] = mapped_column(Float, default=0)
    average_quality: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    results: Mapped[list["EvaluationResult"]] = relationship(cascade="all, delete-orphan")

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id"))
    run_type: Mapped[str] = mapped_column(String(30))
    question_id: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80))
    selected_model: Mapped[str] = mapped_column(String(120))
    cost: Mapped[float] = mapped_column(Float, default=0)
    latency: Mapped[float] = mapped_column(Float, default=0)
    quality: Mapped[float] = mapped_column(Float, default=0)
    correctness: Mapped[float] = mapped_column(Float, default=0)
    relevance: Mapped[float] = mapped_column(Float, default=0)
    completeness: Mapped[float] = mapped_column(Float, default=0)
    clarity: Mapped[float] = mapped_column(Float, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
