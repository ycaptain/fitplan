"""POST /api/plan/generate — generate an initial weekly plan."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class GeneratePlanRequest(BaseModel):
    goal: str = "general"
    split: str = "ppl"
    sessions_per_week: int = 4


class GeneratePlanResponse(BaseModel):
    plan_id: str
    message: str


@router.post("/plan/generate", response_model=GeneratePlanResponse)
async def generate_plan(req: GeneratePlanRequest) -> GeneratePlanResponse:
    return GeneratePlanResponse(
        plan_id="stub-plan-001",
        message=f"TODO: run GA for goal={req.goal}, split={req.split}",
    )
