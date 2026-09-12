from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=List[schemas.MenuItemOut])
def list_menu(db: Session = Depends(get_db)):
    return db.query(models.MenuItem).filter(models.MenuItem.available == 1).all()


@router.post("", response_model=schemas.MenuItemOut)
def add_menu_item(item: schemas.MenuItemCreate, db: Session = Depends(get_db)):
    # NOTE: add an admin-auth dependency here before going to production.
    db_item = models.MenuItem(
        name=item.name,
        category=item.category,
        price=item.price,
        prep_time_minutes=item.prep_time_minutes,
        available=1 if item.available else 0,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def remove_menu_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.MenuItem).get(item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    db_item.available = 0
    db.commit()
    return {"ok": True}
