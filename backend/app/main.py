"""GrowthPilot AI — Tier 2 Core Application Server (system design v2.3 §1), a modular monolith:

- workspace: accounts, RBAC, brand & services (MOD-01/02)
- creative:  Project Creative Workspace — projects, style packs, Kaggle media jobs, publishing
- ai:        Unified AI & LightRAG Engine — LLM router, agents, knowledge (used by both blocks)
- social:    Social & CRM Engine — Meta webhook, inbox, policy engine, CRM, booking, analytics
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import files
from app.core.config import get_settings
from app.creative import projects, publishing_api, styles, worker_api
from app.social import bookings, crm, dashboard, inbox, integrations
from app.workspace import auth, brand, workspaces

app = FastAPI(title="GrowthPilot AI API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTERS = (
    (auth, workspaces, brand),
    (projects, styles, publishing_api, worker_api),
    (integrations, inbox, crm, bookings, dashboard),
    (files,),
)
for group in ROUTERS:
    for module in group:
        app.include_router(module.router, prefix="/api/v1")


@app.get("/healthz")
def healthz():
    return {"ok": True}
