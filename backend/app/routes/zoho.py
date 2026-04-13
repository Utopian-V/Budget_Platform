from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.zoho_service import zoho_client, sync_invoices, sync_sales_orders, sync_credit_notes

router = APIRouter(prefix="/api/zoho", tags=["Zoho Integration"])


@router.get("/status")
def zoho_status():
    return zoho_client.get_status()


@router.post("/sync/invoices")
async def sync_zoho_invoices(db: Session = Depends(get_db)):
    if not zoho_client.is_configured:
        raise HTTPException(status_code=400, detail="Zoho credentials not configured")
    try:
        count = await sync_invoices(db)
        return {"status": "ok", "synced": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/sync/sales-orders")
async def sync_zoho_sales_orders(db: Session = Depends(get_db)):
    if not zoho_client.is_configured:
        raise HTTPException(status_code=400, detail="Zoho credentials not configured")
    try:
        count = await sync_sales_orders(db)
        return {"status": "ok", "synced": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/sync/credit-notes")
async def sync_zoho_credit_notes(db: Session = Depends(get_db)):
    if not zoho_client.is_configured:
        raise HTTPException(status_code=400, detail="Zoho credentials not configured")
    try:
        count = await sync_credit_notes(db)
        return {"status": "ok", "synced": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/sync/all")
async def sync_all_zoho(db: Session = Depends(get_db)):
    if not zoho_client.is_configured:
        raise HTTPException(status_code=400, detail="Zoho credentials not configured")
    results = {}
    try:
        results["invoices"] = await sync_invoices(db)
    except Exception as e:
        results["invoices_error"] = str(e)
    try:
        results["sales_orders"] = await sync_sales_orders(db)
    except Exception as e:
        results["sales_orders_error"] = str(e)
    try:
        results["credit_notes"] = await sync_credit_notes(db)
    except Exception as e:
        results["credit_notes_error"] = str(e)
    return {"status": "ok", "results": results}
