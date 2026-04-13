from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.models import BudgetLine, BudgetMonthly

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/department-variance/{month}")
def department_variance(month: str, db: Session = Depends(get_db)):
    rows = (
        db.query(
            BudgetLine.department,
            BudgetLine.service_category,
            BudgetLine.client_name,
            BudgetLine.manager,
            BudgetMonthly.expected,
            BudgetMonthly.actual,
            BudgetMonthly.mtd_variance,
            BudgetMonthly.reason,
            BudgetMonthly.remark,
        )
        .join(BudgetMonthly, BudgetLine.id == BudgetMonthly.budget_line_id)
        .filter(BudgetMonthly.month == month)
        .order_by(BudgetLine.department, BudgetLine.client_name)
        .all()
    )

    dept_map: dict[str, dict] = {}
    for r in rows:
        dept = r.department or "Unknown"
        if dept not in dept_map:
            dept_map[dept] = {
                "department": dept,
                "total_expected": 0,
                "total_actual": 0,
                "total_variance": 0,
                "lines": [],
            }
        dept_map[dept]["total_expected"] += r.expected or 0
        dept_map[dept]["total_actual"] += r.actual or 0
        dept_map[dept]["total_variance"] += r.mtd_variance or 0
        dept_map[dept]["lines"].append({
            "client_name": r.client_name,
            "service_category": r.service_category,
            "manager": r.manager,
            "expected": r.expected,
            "actual": r.actual,
            "variance": r.mtd_variance,
            "reason": r.reason,
            "remark": r.remark,
        })

    return {"month": month, "departments": list(dept_map.values())}


@router.get("/mtd-ytd")
def mtd_ytd_report(db: Session = Depends(get_db)):
    rows = (
        db.query(
            BudgetLine.department,
            BudgetMonthly.month,
            BudgetMonthly.month_index,
            func.coalesce(func.sum(BudgetMonthly.expected), 0).label("expected"),
            func.coalesce(func.sum(BudgetMonthly.actual), 0).label("actual"),
            func.coalesce(func.sum(BudgetMonthly.mtd_variance), 0).label("mtd_var"),
        )
        .join(BudgetMonthly, BudgetLine.id == BudgetMonthly.budget_line_id)
        .group_by(BudgetLine.department, BudgetMonthly.month, BudgetMonthly.month_index)
        .order_by(BudgetLine.department, BudgetMonthly.month_index)
        .all()
    )

    dept_data: dict[str, dict] = {}
    for r in rows:
        dept = r.department or "Unknown"
        if dept not in dept_data:
            dept_data[dept] = {"department": dept, "months": [], "ytd_expected": 0, "ytd_actual": 0}
        dept_data[dept]["months"].append({
            "month": r.month,
            "month_index": r.month_index,
            "expected": r.expected,
            "actual": r.actual,
            "mtd_variance": r.mtd_var,
        })
        dept_data[dept]["ytd_expected"] += r.expected
        dept_data[dept]["ytd_actual"] += r.actual

    for d in dept_data.values():
        d["ytd_variance"] = d["ytd_expected"] - d["ytd_actual"]

    return list(dept_data.values())


@router.get("/client-summary")
def client_summary(
    department: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            BudgetLine.client_name,
            BudgetLine.department,
            func.coalesce(func.sum(BudgetMonthly.expected), 0).label("total_expected"),
            func.coalesce(func.sum(BudgetMonthly.actual), 0).label("total_actual"),
        )
        .join(BudgetMonthly, BudgetLine.id == BudgetMonthly.budget_line_id)
    )

    if department:
        q = q.filter(BudgetLine.department == department)

    rows = (
        q.group_by(BudgetLine.client_name, BudgetLine.department)
        .order_by(func.sum(BudgetMonthly.expected).desc())
        .all()
    )

    return [
        {
            "client_name": r.client_name,
            "department": r.department,
            "total_expected": r.total_expected,
            "total_actual": r.total_actual,
            "variance": r.total_expected - r.total_actual,
        }
        for r in rows
    ]


@router.get("/true-up-candidates")
def true_up_candidates(
    threshold: float = Query(0.1, description="Variance threshold ratio"),
    db: Session = Depends(get_db),
):
    """Items where cumulative variance exceeds a threshold, suggesting quarterly true-up."""
    rows = (
        db.query(
            BudgetLine.id,
            BudgetLine.client_name,
            BudgetLine.department,
            BudgetLine.service_category,
            BudgetLine.manager,
            func.coalesce(func.sum(BudgetMonthly.expected), 0).label("total_expected"),
            func.coalesce(func.sum(BudgetMonthly.actual), 0).label("total_actual"),
        )
        .join(BudgetMonthly, BudgetLine.id == BudgetMonthly.budget_line_id)
        .group_by(
            BudgetLine.id,
            BudgetLine.client_name,
            BudgetLine.department,
            BudgetLine.service_category,
            BudgetLine.manager,
        )
        .all()
    )

    candidates = []
    for r in rows:
        if r.total_expected == 0:
            continue
        var_ratio = abs(r.total_expected - r.total_actual) / r.total_expected
        if var_ratio >= threshold:
            candidates.append({
                "budget_line_id": r.id,
                "client_name": r.client_name,
                "department": r.department,
                "service_category": r.service_category,
                "manager": r.manager,
                "total_expected": r.total_expected,
                "total_actual": r.total_actual,
                "variance": r.total_expected - r.total_actual,
                "variance_ratio": round(var_ratio, 4),
            })

    candidates.sort(key=lambda x: abs(x["variance"]), reverse=True)
    return candidates


@router.get("/export/{report_type}")
def export_report(
    report_type: str,
    month: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    from app.services.export_service import (
        export_department_variance,
        export_mtd_ytd,
        export_client_summary,
        export_reconciliation,
    )

    if report_type == "department-variance":
        target_month = month or "Apr-25"
        buf = export_department_variance(db, target_month)
        filename = f"department_variance_{target_month}.xlsx"
    elif report_type == "mtd-ytd":
        buf = export_mtd_ytd(db)
        filename = "mtd_ytd_summary.xlsx"
    elif report_type == "client-summary":
        buf = export_client_summary(db)
        filename = "client_summary.xlsx"
    elif report_type == "reconciliation":
        target_month = month or "Apr-25"
        buf = export_reconciliation(db, target_month)
        filename = f"reconciliation_{target_month}.xlsx"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
