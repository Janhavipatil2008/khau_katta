from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, prediction
from ..database import get_db

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/status", response_model=schemas.QueueStatusOut)
def queue_status(db: Session = Depends(get_db)):
    preparing = db.query(models.Order).filter(
        models.Order.status.in_([models.OrderStatus.CONFIRMED, models.OrderStatus.PREPARING])
    ).count()
    ready = db.query(models.Order).filter(models.Order.status == models.OrderStatus.ALMOST_READY).count()
    active_orders = db.query(models.Order).filter(models.Order.status.in_([
        models.OrderStatus.CONFIRMED, models.OrderStatus.PREPARING, models.OrderStatus.ALMOST_READY,
    ])).all()

    avg_wait = (
        sum(o.predicted_prep_time_minutes for o in active_orders) / len(active_orders)
        if active_orders else 0.0
    )

    return schemas.QueueStatusOut(
        people_waiting=len(active_orders),
        orders_preparing=preparing,
        orders_ready=ready,
        average_wait_minutes=round(avg_wait, 1),
        rush_level=prediction.rush_level(len(active_orders)),
    )
