from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.models import SalesOrder, BudgetLine

router = APIRouter(prefix="/api/sales-orders", tags=["Sales Orders"])


def _serialize_so(so: SalesOrder) -> dict:
    return {
        "id": so.id,
        "order_date": str(so.order_date) if so.order_date else None,
        "salesorder_number": so.salesorder_number,
        "status": so.status,
        "customer_name": so.customer_name,
        "billing_entity": so.billing_entity,
        "quotation_no": so.quotation_no,
        "currency_code": so.currency_code,
        "item_name": so.item_name,
        "item_desc": so.item_desc,
        "quantity_ordered": so.quantity_ordered,
        "quantity_invoiced": so.quantity_invoiced,
        "item_price": so.item_price,
        "item_total": so.item_total,
        "department": so.department,
        "sales_person": so.sales_person,
        "unique_code": so.unique_code,
    }


@router.get("")
def list_sales_orders(
    status: Optional[str] = None,
    customer: Optional[str] = None,
    quotation_no: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(SalesOrder)

    if status:
        q = q.filter(SalesOrder.status == status)
    if customer:
        q = q.filter(SalesOrder.customer_name == customer)
    if quotation_no:
        q = q.filter(SalesOrder.quotation_no == quotation_no)

    total = q.count()
    orders = q.order_by(SalesOrder.order_date.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_serialize_so(so) for so in orders],
    }


@router.get("/unlinked")
def unlinked_sales_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    budget_so_numbers = (
        db.query(BudgetLine.sales_order_no)
        .filter(BudgetLine.sales_order_no.isnot(None))
        .distinct()
        .subquery()
    )

    q = db.query(SalesOrder).filter(
        ~SalesOrder.salesorder_number.in_(
            db.query(budget_so_numbers.c.sales_order_no)
        )
    )

    total = q.count()
    orders = q.order_by(SalesOrder.order_date.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_serialize_so(so) for so in orders],
    }
