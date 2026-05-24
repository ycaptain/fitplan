from datetime import UTC, datetime

from fastapi import APIRouter

from app.ai.core.models import (
    Plan,
    ReplanDiff,
    ReplanMetrics,
    ReplanRequest,
    ReplanResult,
    Scores,
)

router = APIRouter()


@router.post("/plan/replan", response_model=ReplanResult)
async def replan(req: ReplanRequest) -> ReplanResult:
    return ReplanResult(
        plan=Plan(
            id=req.plan_id,
            generated_at=datetime.now(UTC).isoformat(),
            sessions=[],
            scores=Scores(),
            strategy_trace=[],
        ),
        diff=ReplanDiff(),
        metrics=ReplanMetrics(),
        reason="",
    )
