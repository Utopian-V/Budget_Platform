from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.models import Invoice, CreditNote

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


@router.get("")
def list_invoices(
    month: Optional[str] = None,
    status: Optional[str] = None,
    customer: Optional[str] = None,
    department: Optional[str] = None,
    billing_entity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Invoice)

    if month:
        q = q.filter(Invoice.invoice_month == month)
    if status:
        q = q.filter(Invoice.invoice_status == status)
    if customer:
        q = q.filter(Invoice.customer_name == customer)
    if department:
        q = q.filter(Invoice.department == department)
    if billing_entity:
        q = q.filter(Invoice.billing_entity == billing_entity)

    total = q.count()
    invoices = q.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "id": inv.id,
                "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
                "invoice_number": inv.invoice_number,
                "invoice_status": inv.invoice_status,
                "customer_name": inv.customer_name,
                "billing_entity": inv.billing_entity,
                "department": inv.department,
                "item_name": inv.item_name,
                "item_total": inv.item_total,
                "subtotal": inv.subtotal,
                "total": inv.total,
                "balance": inv.balance,
                "sales_order_number": inv.sales_order_number,
                "unique_code": inv.unique_code,
                "invoice_month": inv.invoice_month,
                "is_voided": inv.is_voided,
                "cleaned_item_total": inv.cleaned_item_total,
            }
            for inv in invoices
        ],
    }


@router.get("/summary/{month}")
def invoice_summary(month: str, db: Session = Depends(get_db)):
    base = db.query(Invoice).filter(Invoice.invoice_month == month)

    total_amount = base.with_entities(func.coalesce(func.sum(Invoice.total), 0)).scalar()

    voided_count = base.filter(Invoice.is_voided == True).count()  # noqa: E712

    cn_count = db.query(CreditNote).count()
    cn_total = db.query(func.coalesce(func.sum(CreditNote.item_total_adjusted), 0)).scalar()

    net_amount = total_amount + cn_total  # cn_total is negative (sign-flipped)

    return {
        "month": month,
        "total_amount": total_amount,
        "voided_count": voided_count,
        "credit_note_count": cn_count,
        "credit_note_total": cn_total,
        "net_amount": net_amount,
    }


@router.get("/cleanup-report")
def cleanup_report(db: Session = Depends(get_db)):
    voided = (
        db.query(Invoice)
        .filter(Invoice.is_voided == True)  # noqa: E712
        .order_by(Invoice.invoice_date.desc())
        .all()
    )

    credit_notes = (
        db.query(CreditNote)
        .order_by(CreditNote.cn_date.desc())
        .all()
    )

    return {
        "voided_invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
                "customer_name": inv.customer_name,
                "total": inv.total,
                "status": inv.invoice_status,
            }
            for inv in voided
        ],
        "credit_notes": [
            {
                "id": cn.id,
                "cn_number": cn.cn_number,
                "cn_date": str(cn.cn_date) if cn.cn_date else None,
                "customer_name": cn.customer_name,
                "associated_invoice_number": cn.associated_invoice_number,
                "item_total_original": cn.item_total_original,
                "item_total_adjusted": cn.item_total_adjusted,
                "department": cn.department,
            }
            for cn in credit_notes
        ],
    }
