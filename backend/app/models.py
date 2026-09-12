import enum
from datetime import datetime

from sqlalchemy import (Column, Integer, String, Float, DateTime, ForeignKey,
                         Enum, Text)
from sqlalchemy.orm import relationship

from .database import Base


class OrderStatus(str, enum.Enum):
    CONFIRMED = "Confirmed"
    PREPARING = "Preparing"
    ALMOST_READY = "Almost Ready"
    READY = "Ready"
    COLLECTED = "Collected"


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, default="General")
    price = Column(Float, nullable=False)
    prep_time_minutes = Column(Integer, nullable=False, default=5)
    available = Column(Integer, default=1)  # 1 = True, 0 = False (sqlite-friendly)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    token_number = Column(Integer, unique=True, index=True)
    student_name = Column(String, nullable=False)
    group_code = Column(String, nullable=True, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.CONFIRMED)
    predicted_prep_time_minutes = Column(Integer, default=0)
    pickup_window_start = Column(DateTime, nullable=True)
    pickup_window_end = Column(DateTime, nullable=True)
    total_price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    name = Column(String, nullable=False)  # snapshot, in case menu changes later
    quantity = Column(Integer, default=1)
    prep_time_minutes = Column(Integer, default=5)
    price = Column(Float, default=0.0)

    order = relationship("Order", back_populates="items")
