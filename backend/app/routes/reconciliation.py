import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import ReconciliationRecord, MonthlySnapshot, BudgetLine, BudgetMonthly

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])

MONTH_ORDER = [
    "Apr-25", "May-25", "Jun-25", "Jul-25", "Aug-25", "Sep-25",
    "Oct-25", "Nov-25", "Dec-25", "Jan-26", "Feb-26", "Mar-26",
]


def _get_reco_service():
    try:
        from app.services.reconciliation_service import (
            run_reconciliation,
            run_full_reconciliation,
        )
        return run_reconciliation, run_full_reconciliation
    except ImportError:
        return None, None


@router.post("/run/{month}")
def run_reconciliation_month(month: str, db: Session = Depends(get_db)):
    run_reco, _ = _get_reco_service()
    if run_reco is None:
        raise HTTPException(
            status_code=501,
            detail="Reconciliation service not yet implemented",
        )
    result = run_reco(db, month)
    return {"message": f"Reconciliation completed for {month}", "result": result}


@router.post("/run-all")
def run_full_reconciliation(db: Session = Depends(get_db)):
    _, run_full = _get_reco_service()
    if run_full is None:
        raise HTTPException(
            status_code=501,
            detail="Reconciliation service not yet implemented",
        )
    result = run_full(db)
    return {"message": "Full reconciliation completed", "result": result}


@router.get("/summary/{month}")
def reconciliation_summary(month: str, db: Session = Depends(get_db)):
    base = db.query(ReconciliationRecord).filter(ReconciliationRecord.month == month)

    total = base.count()
    matched = base.filter(ReconciliationRecord.is_matched == True).count()  # noqa: E712
    unmatched = total - matched

    total_budget = base.with_entities(
        func.coalesce(func.sum(ReconciliationRecord.budget_amount), 0)
    ).scalar()
    total_invoice = base.with_entities(
        func.coalesce(func.sum(ReconciliationRecord.invoice_amount), 0)
    ).scalar()
    total_diff = base.with_entities(
        func.coalesce(func.sum(ReconciliationRecord.difference), 0)
    ).scalar()

    return {
        "month": month,
        "total_records": total,
        "matched": matched,
        "unmatched": unmatched,
        "total_budget_amount": total_budget,
        "total_invoice_amount": total_invoice,
        "total_difference": total_diff,
    }


@router.get("/unmatched/{month}")
def unmatched_items(month: str, db: Session = Depends(get_db)):
    records = (
        db.query(ReconciliationRecord)
        .filter(
            ReconciliationRecord.month == month,
            ReconciliationRecord.is_matched == False,  # noqa: E712
        )
        .all()
    )

    categorized: dict[str, list] = {}
    for r in records:
        cat = r.discrepancy_type or "Uncategorized"
        categorized.setdefault(cat, []).append({
            "id": r.id,
            "unique_code": r.unique_code,
            "budget_amount": r.budget_amount,
            "invoice_amount": r.invoice_amount,
            "difference": r.difference,
            "detail": r.discrepancy_detail,
        })

    return {"month": month, "categories": categorized}


@router.get("/new-additions/{month}")
def new_additions(month: str, db: Session = Depends(get_db)):
    records = (
        db.query(ReconciliationRecord)
        .filter(
            ReconciliationRecord.month == month,
            ReconciliationRecord.discrepancy_type == "new_addition",
        )
        .all()
    )

    return {
        "month": month,
        "count": len(records),
        "data": [
            {
                "id": r.id,
                "unique_code": r.unique_code,
                "invoice_amount": r.invoice_amount,
                "detail": r.discrepancy_detail,
            }
            for r in records
        ],
    }


@router.post("/snapshot/{month}")
def create_snapshot(month: str, db: Session = Depends(get_db)):
    """Freeze current reconciliation + budget state for a month into a snapshot."""
    reco_records = (
        db.query(ReconciliationRecord)
        .filter(ReconciliationRecord.month == month)
        .all()
    )
    budget_rows = (
        db.query(
            BudgetLine.client_name,
            BudgetLine.department,
            BudgetLine.service_category,
            BudgetMonthly.expected,
            BudgetMonthly.actual,
            BudgetMonthly.mtd_variance,
            BudgetMonthly.ytd_variance,
            BudgetMonthly.reason,
            BudgetMonthly.remark,
        )
        .join(BudgetMonthly, BudgetLine.id == BudgetMonthly.budget_line_id)
        .filter(BudgetMonthly.month == month)
        .all()
    )

    snapshot_data = {
        "month": month,
        "created_at": datetime.utcnow().isoformat(),
        "reconciliation": [
            {
                "unique_code": r.unique_code,
                "budget_amount": r.budget_amount,
                "invoice_amount": r.invoice_amount,
                "difference": r.difference,
                "is_matched": r.is_matched,
                "discrepancy_type": r.discrepancy_type,
            }
            for r in reco_records
        ],
        "budget_actuals": [
            {
                "client_name": r.client_name,
                "department": r.department,
                "service_category": r.service_category,
                "expected": r.expected,
                "actual": r.actual,
                "mtd_variance": r.mtd_variance,
                "ytd_variance": r.ytd_variance,
                "reason": r.reason,
                "remark": r.remark,
            }
            for r in budget_rows
        ],
    }

    snap = MonthlySnapshot(
        month=month,
        snapshot_date=datetime.utcnow(),
        data_json=json.dumps(snapshot_data),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)

    return {"message": f"Snapshot created for {month}", "snapshot_id": snap.id}


@router.get("/snapshots")
def list_snapshots(db: Session = Depends(get_db)):
    snaps = db.query(MonthlySnapshot).order_by(MonthlySnapshot.snapshot_date.desc()).all()
    return [
        {
            "id": s.id,
            "month": s.month,
            "snapshot_date": str(s.snapshot_date) if s.snapshot_date else None,
            "created_by": s.created_by,
        }
        for s in snaps
    ]


@router.get("/snapshot/{snapshot_id}")
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snap = db.query(MonthlySnapshot).filter(MonthlySnapshot.id == snapshot_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {
        "id": snap.id,
        "month": snap.month,
        "snapshot_date": str(snap.snapshot_date) if snap.snapshot_date else None,
        "created_by": snap.created_by,
        "data": json.loads(snap.data_json) if snap.data_json else None,
    }
