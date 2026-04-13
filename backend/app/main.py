import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db
from app.routes import (
    dashboard,
    budget,
    invoices,
    sales_orders,
    proposals,
    reconciliation,
    reports,
    master,
    data_import,
    zoho,
    credit_notes,
)

app = FastAPI(title="Budget Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(dashboard.router)
app.include_router(budget.router)
app.include_router(invoices.router)
app.include_router(sales_orders.router)
app.include_router(proposals.router)
app.include_router(reconciliation.router)
app.include_router(reports.router)
app.include_router(master.router)
app.include_router(data_import.router)
app.include_router(zoho.router)
app.include_router(credit_notes.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Budget Platform API"}


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(STATIC_DIR / "index.html"))
