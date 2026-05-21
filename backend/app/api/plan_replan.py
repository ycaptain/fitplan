"""POST /api/plan/replan — adaptive re-planning."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ReplanRequest(BaseModel):
    plan_id: str
    trigger_type: str = "fixed_event_added"
    payload: dict = {}


class ReplanResponse(BaseModel):
    plan_id: str
    message: str
    diff: dict = {}


@router.post("/plan/replan", response_model=ReplanResponse)
async def replan(req: ReplanRequest) -> ReplanResponse:
    return ReplanResponse(
        plan_id=req.plan_id,
        message=f"TODO: re-validate + replan for trigger={req.trigger_type}",
        diff={"moved": [], "removed": [], "added": []},
    )
