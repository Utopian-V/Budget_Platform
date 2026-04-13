import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/import", tags=["Data Import"])

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
UPLOAD_DIR = Path("/tmp/budget_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _get_import_service():
    try:
        from app.services import import_service
        return import_service
    except ImportError:
        return None


@router.post("/upload/{data_type}")
async def upload_and_import(
    data_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an Excel file and import it. data_type: budget, invoices, sales-orders, credit-notes, proposals"""
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")

    upload_base = UPLOAD_DIR / "current"
    upload_base.mkdir(parents=True, exist_ok=True)

    if data_type == "budget":
        dest = upload_base / "Budget Sheet 2025-26.xlsx"
    elif data_type == "invoices":
        inv_dir = upload_base / "Zoho Exports and Proposal" / "Invoices"
        inv_dir.mkdir(parents=True, exist_ok=True)
        dest = inv_dir / file.filename
    elif data_type == "sales-orders":
        so_dir = upload_base / "Zoho Exports and Proposal" / "Sales Orders"
        so_dir.mkdir(parents=True, exist_ok=True)
        dest = so_dir / file.filename
    elif data_type == "credit-notes":
        cn_dir = upload_base / "Zoho Exports and Proposal" / "Credit Notes"
        cn_dir.mkdir(parents=True, exist_ok=True)
        dest = cn_dir / file.filename
    elif data_type == "proposals":
        prop_dir = upload_base / "Zoho Exports and Proposal"
        prop_dir.mkdir(parents=True, exist_ok=True)
        dest = prop_dir / "Proposal FY 25-26_Automation.xlsx"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown data type: {data_type}")

    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        base = str(upload_base)
        if data_type == "budget":
            svc.import_master_data(db, base)
            svc.import_budget_sheet(db, base)
        elif data_type == "invoices":
            svc.import_invoices(db, base)
        elif data_type == "sales-orders":
            svc.import_sales_orders(db, base)
        elif data_type == "credit-notes":
            svc.import_credit_notes(db, base)
        elif data_type == "proposals":
            svc.import_proposals(db, base)
        db.commit()
        return {"message": f"{data_type} imported successfully from uploaded file"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-all")
async def upload_all_files(
    budget: UploadFile = File(None),
    invoices: list[UploadFile] = File(None),
    sales_orders: list[UploadFile] = File(None),
    credit_notes: list[UploadFile] = File(None),
    proposals: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    """Upload multiple Excel files at once."""
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")

    upload_base = UPLOAD_DIR / "current"
    results = {}

    if budget:
        dest = upload_base / "Budget Sheet 2025-26.xlsx"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(await budget.read())
        try:
            svc.import_master_data(db, str(upload_base))
            svc.import_budget_sheet(db, str(upload_base))
            results["budget"] = "ok"
        except Exception as e:
            results["budget_error"] = str(e)

    for label, files, importer in [
        ("invoices", invoices, svc.import_invoices),
        ("sales_orders", sales_orders, svc.import_sales_orders),
        ("credit_notes", credit_notes, svc.import_credit_notes),
    ]:
        if files:
            sub = "Invoices" if label == "invoices" else "Sales Orders" if label == "sales_orders" else "Credit Notes"
            target_dir = upload_base / "Zoho Exports and Proposal" / sub
            target_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                with open(target_dir / f.filename, "wb") as out:
                    out.write(await f.read())
            try:
                importer(db, str(upload_base))
                results[label] = "ok"
            except Exception as e:
                results[f"{label}_error"] = str(e)

    if proposals:
        prop_dir = upload_base / "Zoho Exports and Proposal"
        prop_dir.mkdir(parents=True, exist_ok=True)
        dest = prop_dir / "Proposal FY 25-26_Automation.xlsx"
        with open(dest, "wb") as f:
            f.write(await proposals.read())
        try:
            svc.import_proposals(db, str(upload_base))
            results["proposals"] = "ok"
        except Exception as e:
            results["proposals_error"] = str(e)

    db.commit()
    return {"status": "ok", "results": results}


@router.post("/all")
def import_all(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")

    upload_base = UPLOAD_DIR / "current"
    use_path = str(upload_base) if upload_base.is_dir() else BASE_PATH

    try:
        result = svc.import_all(db, use_path)
        return {"message": "All data imported successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget")
def import_budget(db: Session = Depends(get_db)):
    svc = _get_import_service()
    if svc is None:
        raise HTTPException(status_code=501, detail="Import service not available")
    upload_base = UPLOAD_DIR / "current"
    use_path = str(upload_base) if upload_base.is_dir() else BASE_PATH
    try:
        svc.import_master_data(db, use_path)
        svc.import_budget_sheet(db, use_path)
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
    upload_base = UPLOAD_DIR / "current"
    use_path = str(upload_base) if upload_base.is_dir() else BASE_PATH
    try:
        svc.import_invoices(db, use_path)
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
    upload_base = UPLOAD_DIR / "current"
    use_path = str(upload_base) if upload_base.is_dir() else BASE_PATH
    try:
        svc.import_sales_orders(db, use_path)
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
    upload_base = UPLOAD_DIR / "current"
    use_path = str(upload_base) if upload_base.is_dir() else BASE_PATH
    try:
        svc.import_credit_notes(db, use_path)
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
    upload_base = UPLOAD_DIR / "current"
    use_path = str(upload_base) if upload_base.is_dir() else BASE_PATH
    try:
        svc.import_proposals(db, use_path)
        db.commit()
        return {"message": "Proposals imported"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
