from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.models import BudgetLine, BudgetMonthly, BudgetLevel, ReconciliationRecord

router = APIRouter(prefix="/api/budget", tags=["Budget"])


class BudgetLineUpdate(BaseModel):
    remarks: Optional[str] = None
    manager: Optional[str] = None
    partner: Optional[str] = None
    billing_frequency: Optional[str] = None


class VarianceUpdate(BaseModel):
    reason: Optional[str] = None
    remark: Optional[str] = None


def _serialize_budget_line(bl: BudgetLine) -> dict:
    return {
        "id": bl.id,
        "serial_no": bl.serial_no,
        "level": bl.level.value if bl.level else None,
        "quotation_no": bl.quotation_no,
        "sales_order_no": bl.sales_order_no,
        "client_name": bl.client_name,
        "billing_type": bl.billing_type,
        "billing_entity": bl.billing_entity,
        "partner": bl.partner,
        "manager": bl.manager,
        "department": bl.department,
        "service_category": bl.service_category,
        "service_description": bl.service_description,
        "billing_frequency": bl.billing_frequency,
        "no_of_billing": bl.no_of_billing,
        "currency": bl.currency,
        "exchange_rate": bl.exchange_rate,
        "existing_fees": bl.existing_fees,
        "pct_increase": bl.pct_increase,
        "increased_fees": bl.increased_fees,
        "fee_for_sales_order": bl.fee_for_sales_order,
        "sales_order_value": bl.sales_order_value,
        "variance": bl.variance,
        "amount_carried_forward": bl.amount_carried_forward,
        "remarks": bl.remarks,
        "monthly_data": [
            {
                "id": m.id,
                "month": m.month,
                "month_index": m.month_index,
                "expected": m.expected,
                "actual": m.actual,
                "mtd_variance": m.mtd_variance,
                "ytd_variance": m.ytd_variance,
                "reason": m.reason,
                "remark": m.remark,
            }
            for m in sorted(bl.monthly_data, key=lambda x: x.month_index)
        ],
    }


@router.get("/lines")
def list_budget_lines(
    department: Optional[str] = None,
    manager: Optional[str] = None,
    client: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(BudgetLine).options(joinedload(BudgetLine.monthly_data))

    if department:
        q = q.filter(BudgetLine.department == department)
    if manager:
        q = q.filter(BudgetLine.manager == manager)
    if client:
        q = q.filter(BudgetLine.client_name == client)
    if level:
        q = q.filter(BudgetLine.level == level)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                BudgetLine.client_name.ilike(pattern),
                BudgetLine.service_description.ilike(pattern),
                BudgetLine.quotation_no.ilike(pattern),
                BudgetLine.sales_order_no.ilike(pattern),
            )
        )

    total = q.count()
    lines = q.offset(skip).limit(limit).all()

    seen_ids = set()
    unique_lines = []
    for bl in lines:
        if bl.id not in seen_ids:
            seen_ids.add(bl.id)
            unique_lines.append(bl)

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_serialize_budget_line(bl) for bl in unique_lines],
    }


@router.get("/lines/{line_id}")
def get_budget_line(line_id: int, db: Session = Depends(get_db)):
    bl = (
        db.query(BudgetLine)
        .options(joinedload(BudgetLine.monthly_data))
        .filter(BudgetLine.id == line_id)
        .first()
    )
    if not bl:
        raise HTTPException(status_code=404, detail="Budget line not found")
    return _serialize_budget_line(bl)


@router.put("/lines/{line_id}")
def update_budget_line(
    line_id: int,
    body: BudgetLineUpdate,
    db: Session = Depends(get_db),
):
    bl = db.query(BudgetLine).filter(BudgetLine.id == line_id).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Budget line not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bl, key, value)

    db.commit()
    db.refresh(bl)
    return {"message": "Updated", "id": bl.id}


@router.get("/variance")
def get_variance(
    department: Optional[str] = None,
    month: Optional[str] = None,
    budget_line_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = (
        db.query(BudgetMonthly, BudgetLine)
        .join(BudgetLine, BudgetMonthly.budget_line_id == BudgetLine.id)
    )

    if department:
        q = q.filter(BudgetLine.department == department)
    if month:
        q = q.filter(BudgetMonthly.month == month)
    if budget_line_id:
        q = q.filter(BudgetMonthly.budget_line_id == budget_line_id)

    total = q.count()
    rows = q.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "budget_line_id": bl.id,
                "client_name": bl.client_name,
                "department": bl.department,
                "service_category": bl.service_category,
                "month": bm.month,
                "month_index": bm.month_index,
                "expected": bm.expected,
                "actual": bm.actual,
                "mtd_variance": bm.mtd_variance,
                "ytd_variance": bm.ytd_variance,
                "reason": bm.reason,
                "remark": bm.remark,
            }
            for bm, bl in rows
        ],
    }


@router.put("/variance/{budget_line_id}/{month}")
def update_variance(
    budget_line_id: int,
    month: str,
    body: VarianceUpdate,
    db: Session = Depends(get_db),
):
    bm = (
        db.query(BudgetMonthly)
        .filter(
            BudgetMonthly.budget_line_id == budget_line_id,
            BudgetMonthly.month == month,
        )
        .first()
    )
    if not bm:
        raise HTTPException(status_code=404, detail="Monthly record not found")

    if body.reason is not None:
        bm.reason = body.reason
    if body.remark is not None:
        bm.remark = body.remark

    db.commit()
    db.refresh(bm)
    return {"message": "Updated", "budget_line_id": budget_line_id, "month": month}


class PromoteRequest(BaseModel):
    reconciliation_record_id: int


MONTH_LABELS = [
    "Apr-25", "May-25", "Jun-25", "Jul-25", "Aug-25", "Sep-25",
    "Oct-25", "Nov-25", "Dec-25", "Jan-26", "Feb-26", "Mar-26",
]


@router.post("/promote")
def promote_new_addition(
    body: PromoteRequest,
    db: Session = Depends(get_db),
):
    """Promote a new-addition reconciliation record to a Level 2 budget line."""
    reco = (
        db.query(ReconciliationRecord)
        .filter(ReconciliationRecord.id == body.reconciliation_record_id)
        .first()
    )
    if not reco:
        raise HTTPException(status_code=404, detail="Reconciliation record not found")

    parts = (reco.unique_code or "").split("|", 1)
    so_number = parts[0] if parts else None
    service_cat = parts[1] if len(parts) > 1 else None

    bl = BudgetLine(
        level=BudgetLevel.NEW_ADDITION,
        sales_order_no=so_number,
        service_category=service_cat,
        client_name=reco.discrepancy_detail,
        unique_code_so=reco.unique_code,
        unique_code_invoice=reco.unique_code,
    )
    db.add(bl)
    db.flush()

    for idx, m in enumerate(MONTH_LABELS):
        expected = reco.invoice_amount if m == reco.month else 0
        bm = BudgetMonthly(
            budget_line_id=bl.id,
            month=m,
            month_index=idx,
            expected=expected,
            actual=reco.invoice_amount if m == reco.month else 0,
        )
        db.add(bm)

    db.commit()
    return {"message": "Promoted to Level 2 budget line", "budget_line_id": bl.id}
