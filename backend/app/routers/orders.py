import random
import string
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, prediction
from ..database import get_db
from ..ws_manager import manager

router = APIRouter(prefix="/orders", tags=["orders"])

ACTIVE_STATUSES = [
    models.OrderStatus.CONFIRMED,
    models.OrderStatus.PREPARING,
    models.OrderStatus.ALMOST_READY,
]


def _pending_orders_count(db: Session) -> int:
    return db.query(models.Order).filter(models.Order.status.in_(ACTIVE_STATUSES)).count()


def _next_token_number(db: Session) -> int:
    last = db.query(models.Order).order_by(models.Order.id.desc()).first()
    return (last.token_number + 1) if last else 1


def _build_order(db: Session, payload: schemas.OrderCreate, group_code: Optional[str] = None) -> models.Order:
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    menu_ids = [i.menu_item_id for i in payload.items]
    menu_items = {m.id: m for m in db.query(models.MenuItem).filter(models.MenuItem.id.in_(menu_ids)).all()}

    order_items = []
    item_prep_times = []
    total_price = 0.0
    for entry in payload.items:
        menu_item = menu_items.get(entry.menu_item_id)
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item {entry.menu_item_id} not found")
        order_items.append(models.OrderItem(
            menu_item_id=menu_item.id,
            name=menu_item.name,
            quantity=entry.quantity,
            prep_time_minutes=menu_item.prep_time_minutes,
            price=menu_item.price * entry.quantity,
        ))
        item_prep_times.extend([menu_item.prep_time_minutes] * entry.quantity)
        total_price += menu_item.price * entry.quantity

    pending_count = _pending_orders_count(db)
    predicted_minutes = prediction.estimate_prep_time(item_prep_times, pending_count)
    window_start, window_end = prediction.pickup_window(predicted_minutes)

    order = models.Order(
        token_number=_next_token_number(db),
        student_name=payload.student_name,
        group_code=group_code or payload.group_code,
        status=models.OrderStatus.CONFIRMED,
        predicted_prep_time_minutes=predicted_minutes,
        pickup_window_start=window_start,
        pickup_window_end=window_end,
        total_price=total_price,
        items=order_items,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.post("", response_model=schemas.OrderOut)
async def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    order = _build_order(db, payload)
    await manager.broadcast({"event": "new_order", "token_number": order.token_number})
    return order


@router.post("/group", response_model=List[schemas.OrderOut])
async def create_group_order(payloads: List[schemas.OrderCreate], db: Session = Depends(get_db)):
    """Each friend submits their own items; all get tagged with one shared group_code."""
    if not payloads:
        raise HTTPException(status_code=400, detail="Group order needs at least one member")
    group_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    orders = [_build_order(db, p, group_code=group_code) for p in payloads]
    await manager.broadcast({"event": "new_group_order", "group_code": group_code})
    return orders


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("", response_model=List[schemas.OrderOut])
def list_orders(status: Optional[models.OrderStatus] = None, db: Session = Depends(get_db)):
    query = db.query(models.Order)
    if status:
        query = query.filter(models.Order.status == status)
    return query.order_by(models.Order.created_at.desc()).all()


@router.patch("/{order_id}/status", response_model=schemas.OrderOut)
async def update_order_status(order_id: int, payload: schemas.OrderStatusUpdate, db: Session = Depends(get_db)):
    # NOTE: add an admin-auth dependency here before going to production.
    order = db.query(models.Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    await manager.broadcast({
        "event": "status_update",
        "order_id": order.id,
        "token_number": order.token_number,
        "status": order.status.value,
    })
    return order
