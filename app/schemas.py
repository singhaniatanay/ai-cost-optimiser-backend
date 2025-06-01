# Pydantic request/response models (stub) 
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    answer: str

# New schemas for interactive mode
class WorkloadParams(BaseModel):
    calls_per_day: int
    avg_input_tokens: int
    avg_output_tokens: int
    latency_sla_ms: int
    region: str
    compliance_constraints: List[str]
    current_model: str

class CostModel(BaseModel):
    model_name: str
    monthly_cost: float
    p90_latency_ms: int
    context_window_tokens: int

class RankedModel(BaseModel):
    model_name: str
    monthly_cost: float
    p90_latency_ms: int
    composite_score: float

class ROIAnalysis(BaseModel):
    current_model: str
    best_model: str
    savings_per_month: float
    roi_percent: float
    payback_weeks: int

class StructuredResponse(BaseModel):
    solution_architect: Optional[Dict[str, Any]] = None
    workload_params: WorkloadParams
    cost_table: List[CostModel]
    ranked_models: List[RankedModel]
    roi_analysis: ROIAnalysis
    final_recommendation: str
    editable_fields: List[str] = ["calls_per_day", "avg_input_tokens", "avg_output_tokens", "latency_sla_ms", "region"]

class InteractiveRequest(BaseModel):
    # Modified parameters - only provide fields that were changed
    modified_workload: Optional[WorkloadParams] = None
    # Original data to restart from appropriate step
    original_data: Optional[Dict[str, Any]] = None
    # For initial requests (same as ChatRequest)
    messages: Optional[List[Message]] = None

class InteractiveResponse(BaseModel):
    # Either structured data or simple answer for greetings/errors
    structured_data: Optional[StructuredResponse] = None
    simple_answer: Optional[str] = None 