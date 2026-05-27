from fastapi import APIRouter

from app.ai.core.models import GeneratePlanRequest, Plan
from app.ai.csp.backtracking import generate_initial_plan
from app.api import plan_store

router = APIRouter()


@router.post("/plan/generate", response_model=Plan)
async def generate_plan(req: GeneratePlanRequest) -> Plan:
    plan = generate_initial_plan(req)
    plan_store.put(plan, req.fixed_events)
    return plan
