from datetime import UTC, datetime

from fastapi import APIRouter

from app.ai.core.models import GeneratePlanRequest, Plan, Scores

router = APIRouter()


@router.post("/plan/generate", response_model=Plan)
async def generate_plan(req: GeneratePlanRequest) -> Plan:
    return Plan(
        id="stub-plan-001",
        generated_at=datetime.now(UTC).isoformat(),
        sessions=[],
        scores=Scores(),
        strategy_trace=[],
    )
