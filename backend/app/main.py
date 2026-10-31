from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    bookings,
    brand,
    crm,
    dashboard,
    files,
    inbox,
    integrations,
    projects,
    publishing,
    styles,
    worker_api,
    workspaces,
)
from app.config import get_settings

app = FastAPI(title="GrowthPilot AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    auth,
    workspaces,
    brand,
    integrations,
    inbox,
    crm,
    bookings,
    dashboard,
    projects,
    styles,
    publishing,
    worker_api,
    files,
):
    app.include_router(module.router, prefix="/api/v1")


@app.get("/healthz")
def healthz():
    return {"ok": True}
