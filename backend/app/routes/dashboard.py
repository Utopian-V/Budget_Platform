from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import BudgetLine, BudgetMonthly, Invoice, Proposal, Client

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

MONTH_LABELS = [
    "Apr", "May", "Jun", "Jul", "Aug", "Sep",
    "Oct", "Nov", "Dec", "Jan", "Feb", "Mar",
]


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_budget = db.query(func.coalesce(func.sum(BudgetMonthly.expected), 0)).scalar()
    total_actual_ytd = db.query(func.coalesce(func.sum(BudgetMonthly.actual), 0)).scalar()
    total_variance_ytd = total_budget - total_actual_ytd

    total_clients = db.query(Client).count()
    total_invoices = db.query(Invoice).count()
    total_proposals = db.query(Proposal).count()

    monthly_expected = []
    monthly_actual = []
    for idx in range(12):
        exp = (
            db.query(func.coalesce(func.sum(BudgetMonthly.expected), 0))
            .filter(BudgetMonthly.month_index == idx)
            .scalar()
        )
        act = (
            db.query(func.coalesce(func.sum(BudgetMonthly.actual), 0))
            .filter(BudgetMonthly.month_index == idx)
            .scalar()
        )
        monthly_expected.append(exp)
        monthly_actual.append(act)

    return {
        "total_budget": total_budget,
        "total_actual_ytd": total_actual_ytd,
        "total_variance_ytd": total_variance_ytd,
        "total_clients": total_clients,
        "total_invoices": total_invoices,
        "total_proposals": total_proposals,
        "monthly_expected": monthly_expected,
        "monthly_actual": monthly_actual,
    }


@router.get("/department-summary")
def department_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(
            BudgetLine.department,
            func.coalesce(func.sum(BudgetMonthly.expected), 0).label("budget"),
            func.coalesce(func.sum(BudgetMonthly.actual), 0).label("actual"),
        )
        .join(BudgetMonthly, BudgetLine.id == BudgetMonthly.budget_line_id)
        .group_by(BudgetLine.department)
        .all()
    )
    return [
        {
            "department": r.department,
            "budget": r.budget,
            "actual": r.actual,
            "variance": r.budget - r.actual,
        }
        for r in rows
    ]


@router.get("/recent-activity")
def recent_activity(db: Session = Depends(get_db)):
    invoices = (
        db.query(Invoice)
        .order_by(Invoice.invoice_date.desc())
        .limit(20)
        .all()
    )
    proposals = (
        db.query(Proposal)
        .order_by(Proposal.created_at.desc())
        .limit(20)
        .all()
    )

    activity = []
    for inv in invoices:
        activity.append({
            "type": "invoice",
            "date": str(inv.invoice_date) if inv.invoice_date else None,
            "reference": inv.invoice_number,
            "customer": inv.customer_name,
            "amount": inv.total,
            "status": inv.invoice_status,
        })
    for prop in proposals:
        activity.append({
            "type": "proposal",
            "date": str(prop.created_at) if prop.created_at else None,
            "reference": prop.quotation_no,
            "customer": prop.customer_name,
            "amount": prop.fee_proposed,
            "status": prop.status,
        })

    activity.sort(key=lambda x: x["date"] or "", reverse=True)
    return activity[:20]
