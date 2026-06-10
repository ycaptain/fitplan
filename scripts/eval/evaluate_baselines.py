import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend"))

from app.ai.csp.backtracking import generate_initial_plan
from app.ai.baselines.greedy import generate_greedy_baseline
from app.ai.core.models import GeneratePlanRequest, Preferences

req = GeneratePlanRequest(
    goal="general",
    split="ppl",
    sessions_per_week=4,
    preferences=Preferences(),
)

csp_plan = generate_initial_plan(req)
greedy_plan = generate_greedy_baseline(req)


def print_plan(name, plan):
    print(f"\n=== {name} ===")
    print("score:", plan.scores.total)
    print("recovery:", plan.scores.recovery)
    print("conflicts:", plan.scores.conflicts)
    print("nodes:", plan.strategy_trace[-1].nodes)

    for session in plan.sessions:
        print(
            f"day {session.day}: "
            f"{session.session_type_id} "
            f"{session.start} "
            f"{session.duration_min}min"
        )


print_plan("CSP planner", csp_plan)
print_plan("Greedy baseline", greedy_plan)