from fastapi import APIRouter

from app.ai import baselines as _baselines  # noqa: F401
from app.ai import csp as _csp  # noqa: F401
from app.ai import search as _search  # noqa: F401
from app.ai.core import registry
from app.ai.core.explain import explain_plan
from app.ai.core.models import GeneratePlanRequest, Plan
from app.api import plan_store

router = APIRouter()


@router.post("/plan/generate", response_model=Plan)
async def generate_plan(req: GeneratePlanRequest) -> Plan:
    generator = registry.get(req.algorithm)
    plan = generator(req)
    plan.explanation = explain_plan(plan, [])
    plan_store.put(plan, req.fixed_events)
    return plan
