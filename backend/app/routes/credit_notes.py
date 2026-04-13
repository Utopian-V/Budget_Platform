from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.models import CreditNote

router = APIRouter(prefix="/api/credit-notes", tags=["Credit Notes"])


@router.get("")
def list_credit_notes(
    customer: Optional[str] = None,
    department: Optional[str] = None,
    billing_entity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(CreditNote)

    if customer:
        q = q.filter(CreditNote.customer_name == customer)
    if department:
        q = q.filter(CreditNote.department == department)
    if billing_entity:
        q = q.filter(CreditNote.billing_entity == billing_entity)

    total = q.count()
    notes = q.order_by(CreditNote.cn_date.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "id": cn.id,
                "cn_date": str(cn.cn_date) if cn.cn_date else None,
                "cn_number": cn.cn_number,
                "cn_status": cn.cn_status,
                "customer_name": cn.customer_name,
                "billing_entity": cn.billing_entity,
                "associated_invoice_number": cn.associated_invoice_number,
                "item_name": cn.item_name,
                "item_total_original": cn.item_total_original,
                "item_total_adjusted": cn.item_total_adjusted,
                "department": cn.department,
                "purchase_order": cn.purchase_order,
            }
            for cn in notes
        ],
    }
