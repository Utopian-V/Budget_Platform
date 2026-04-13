from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.models import Proposal, PipelineEntry

router = APIRouter(prefix="/api", tags=["Proposals"])


def _serialize_proposal(p: Proposal) -> dict:
    return {
        "id": p.id,
        "serial_no": p.serial_no,
        "sub_no": p.sub_no,
        "year": p.year,
        "month": p.month,
        "week": p.week,
        "period": p.period,
        "billing_entity": p.billing_entity,
        "customer_name": p.customer_name,
        "service_description": p.service_description,
        "service_category": p.service_category,
        "department": p.department,
        "fee_proposed": p.fee_proposed,
        "status": p.status,
        "follow_up": p.follow_up,
        "pic_for_so": p.pic_for_so,
        "quotation_no": p.quotation_no,
        "so_number": p.so_number,
        "remarks": p.remarks,
        "additional_remarks": p.additional_remarks,
        "days_since_proposal": p.days_since_proposal,
        "is_stale": p.is_stale,
        "created_at": str(p.created_at) if p.created_at else None,
    }


@router.get("/proposals")
def list_proposals(
    status: Optional[str] = None,
    customer: Optional[str] = None,
    billing_entity: Optional[str] = None,
    department: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Proposal)

    if status:
        q = q.filter(Proposal.status == status)
    if customer:
        q = q.filter(Proposal.customer_name == customer)
    if billing_entity:
        q = q.filter(Proposal.billing_entity == billing_entity)
    if department:
        q = q.filter(Proposal.department == department)

    total = q.count()
    proposals = q.order_by(Proposal.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_serialize_proposal(p) for p in proposals],
    }


@router.get("/proposals/stats")
def proposal_stats(db: Session = Depends(get_db)):
    total = db.query(Proposal).count()

    accepted = db.query(Proposal).filter(Proposal.status == "Accepted").count()
    rejected = db.query(Proposal).filter(Proposal.status == "Rejected").count()
    follow_up = db.query(Proposal).filter(Proposal.status == "Follow up").count()

    fee_by_status = (
        db.query(
            Proposal.status,
            func.coalesce(func.sum(Proposal.fee_proposed), 0).label("total_fee"),
        )
        .group_by(Proposal.status)
        .all()
    )

    return {
        "total_proposals": total,
        "accepted_count": accepted,
        "rejected_count": rejected,
        "follow_up_count": follow_up,
        "fee_by_status": [
            {"status": row.status, "total_fee": row.total_fee}
            for row in fee_by_status
        ],
    }


@router.get("/proposals/aging")
def proposal_aging(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Proposal).filter(Proposal.status == "Follow up")
    total = q.count()
    proposals = q.order_by(Proposal.days_since_proposal.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                **_serialize_proposal(p),
                "aging_days": p.days_since_proposal,
                "stale": p.is_stale,
            }
            for p in proposals
        ],
    }


@router.get("/pipeline")
def list_pipeline(
    status: Optional[str] = None,
    department: Optional[str] = None,
    billing_entity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(PipelineEntry)

    if status:
        q = q.filter(PipelineEntry.status == status)
    if department:
        q = q.filter(PipelineEntry.department == department)
    if billing_entity:
        q = q.filter(PipelineEntry.billing_entity == billing_entity)

    total = q.count()
    entries = q.order_by(PipelineEntry.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "id": e.id,
                "year": e.year,
                "week": e.week,
                "period": e.period,
                "billing_entity": e.billing_entity,
                "client_name": e.client_name,
                "discussion": e.discussion,
                "department": e.department,
                "follow_up": e.follow_up,
                "status": e.status,
                "remarks": e.remarks,
            }
            for e in entries
        ],
    }
