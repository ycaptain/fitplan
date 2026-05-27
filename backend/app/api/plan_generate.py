from fastapi import APIRouter

from app.ai.core.models import GeneratePlanRequest, Plan
from app.ai.csp.backtracking import generate_initial_plan

router = APIRouter()


@router.post("/plan/generate", response_model=Plan)
async def generate_plan(req: GeneratePlanRequest) -> Plan:
    return generate_initial_plan(req)