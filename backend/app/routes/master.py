from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.models import (
    Client,
    Department,
    Manager,
    Partner,
    ServiceCategory,
    BillingEntity,
    VarianceReason,
)

router = APIRouter(prefix="/api/master", tags=["Master Data"])

MODEL_MAP = {
    "clients": Client,
    "departments": Department,
    "managers": Manager,
    "partners": Partner,
    "billing-entities": BillingEntity,
}

NAME_FIELD_MAP = {
    "clients": "name",
    "departments": "name",
    "managers": "name",
    "partners": "name",
    "billing-entities": "name",
    "service-categories": "name",
    "variance-reasons": "reason",
}


class MasterItemCreate(BaseModel):
    name: str
    department_id: Optional[int] = None


class MasterItemUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None


def _get_model(entity_type: str):
    if entity_type in MODEL_MAP:
        return MODEL_MAP[entity_type]
    if entity_type == "service-categories":
        return ServiceCategory
    if entity_type == "variance-reasons":
        return VarianceReason
    return None


@router.get("/clients")
def list_clients(db: Session = Depends(get_db)):
    rows = db.query(Client).order_by(Client.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    rows = db.query(Department).order_by(Department.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/managers")
def list_managers(db: Session = Depends(get_db)):
    rows = db.query(Manager).order_by(Manager.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/partners")
def list_partners(db: Session = Depends(get_db)):
    rows = db.query(Partner).order_by(Partner.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/service-categories")
def list_service_categories(db: Session = Depends(get_db)):
    rows = db.query(ServiceCategory).order_by(ServiceCategory.name).all()
    return [{"id": r.id, "name": r.name, "department_id": r.department_id} for r in rows]


@router.get("/billing-entities")
def list_billing_entities(db: Session = Depends(get_db)):
    rows = db.query(BillingEntity).order_by(BillingEntity.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/variance-reasons")
def list_variance_reasons(db: Session = Depends(get_db)):
    rows = db.query(VarianceReason).order_by(VarianceReason.reason).all()
    return [{"id": r.id, "reason": r.reason} for r in rows]


@router.post("/{entity_type}")
def create_master_item(
    entity_type: str,
    body: MasterItemCreate,
    db: Session = Depends(get_db),
):
    model = _get_model(entity_type)
    if model is None:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")

    if entity_type == "variance-reasons":
        obj = VarianceReason(reason=body.name)
    elif entity_type == "service-categories":
        obj = ServiceCategory(name=body.name, department_id=body.department_id)
    else:
        obj = model(name=body.name)

    db.add(obj)
    db.commit()
    db.refresh(obj)

    name_field = NAME_FIELD_MAP.get(entity_type, "name")
    return {"id": obj.id, name_field: getattr(obj, name_field)}


@router.put("/{entity_type}/{item_id}")
def update_master_item(
    entity_type: str,
    item_id: int,
    body: MasterItemUpdate,
    db: Session = Depends(get_db),
):
    model = _get_model(entity_type)
    if model is None:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")

    obj = db.query(model).filter(model.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")

    if body.name is not None:
        name_field = NAME_FIELD_MAP.get(entity_type, "name")
        setattr(obj, name_field, body.name)

    if entity_type == "service-categories" and body.department_id is not None:
        obj.department_id = body.department_id

    db.commit()
    db.refresh(obj)

    name_field = NAME_FIELD_MAP.get(entity_type, "name")
    return {"id": obj.id, name_field: getattr(obj, name_field)}


@router.delete("/{entity_type}/{item_id}")
def delete_master_item(
    entity_type: str,
    item_id: int,
    db: Session = Depends(get_db),
):
    model = _get_model(entity_type)
    if model is None:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")

    obj = db.query(model).filter(model.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(obj)
    db.commit()
    return {"message": "Deleted", "id": item_id}
