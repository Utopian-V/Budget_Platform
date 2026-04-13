import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/import", tags=["Data Import"])

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _get_import_service():
    try:
        from app.services import import_service
        return import_service
    except ImportError:
        return None


@router.post("/all")
def import_all(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")
    try:
        result = svc.import_all(db, BASE_PATH)
        return {"message": "All data imported successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget")
def import_budget(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")
    try:
        svc.import_master_data(db, BASE_PATH)
        svc.import_budget_sheet(db, BASE_PATH)
        db.commit()
        return {"message": "Budget data imported"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoices")
def import_invoices(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")
    try:
        svc.import_invoices(db, BASE_PATH)
        db.commit()
        return {"message": "Invoices imported"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales-orders")
def import_sales_orders(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")
    try:
        svc.import_sales_orders(db, BASE_PATH)
        db.commit()
        return {"message": "Sales orders imported"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/credit-notes")
def import_credit_notes(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")
    try:
        svc.import_credit_notes(db, BASE_PATH)
        db.commit()
        return {"message": "Credit notes imported"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals")
def import_proposals(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")
    try:
        svc.import_proposals(db, BASE_PATH)
        db.commit()
        return {"message": "Proposals imported"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
