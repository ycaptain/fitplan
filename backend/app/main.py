from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import plan_generate, plan_replan

app = FastAPI(
    title="FitPlan AI",
    description="Adaptive AI workout scheduling assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plan_generate.router, prefix="/api", tags=["plan"])
app.include_router(plan_replan.router, prefix="/api", tags=["plan"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
