from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .models import OrderStatus


# ---------- Menu ----------
class MenuItemBase(BaseModel):
    name: str
    category: str = "General"
    price: float
    prep_time_minutes: int = 5
    available: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemOut(MenuItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Orders ----------
class OrderItemIn(BaseModel):
    menu_item_id: int
    quantity: int = 1


class OrderCreate(BaseModel):
    student_name: str
    items: List[OrderItemIn]
    group_code: Optional[str] = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    quantity: int
    prep_time_minutes: int
    price: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    token_number: int
    student_name: str
    group_code: Optional[str]
    status: OrderStatus
    predicted_prep_time_minutes: int
    pickup_window_start: Optional[datetime]
    pickup_window_end: Optional[datetime]
    total_price: float
    created_at: datetime
    items: List[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ---------- Queue ----------
class QueueStatusOut(BaseModel):
    people_waiting: int
    orders_preparing: int
    orders_ready: int
    average_wait_minutes: float
    rush_level: str
