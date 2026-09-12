from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import Base, engine, SessionLocal
from .routers import menu, orders, queue
from .ws_manager import manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Khau Katta API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(queue.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws/orders")
async def orders_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping from client
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def seed_menu_if_empty():
    db = SessionLocal()
    try:
        if db.query(models.MenuItem).count() == 0:
            db.add_all([
                models.MenuItem(name="Veg Cheese Sandwich", category="Snacks", price=40, prep_time_minutes=8),
                models.MenuItem(name="Masala Dosa", category="Main", price=60, prep_time_minutes=12),
                models.MenuItem(name="Veg Biryani", category="Main", price=80, prep_time_minutes=15),
                models.MenuItem(name="Tea", category="Beverages", price=10, prep_time_minutes=2),
                models.MenuItem(name="Vada Pav", category="Snacks", price=20, prep_time_minutes=5),
                models.MenuItem(name="Cold Coffee", category="Beverages", price=35, prep_time_minutes=4),
            ])
            db.commit()
    finally:
        db.close()


seed_menu_if_empty()
