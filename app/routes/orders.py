from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.order import WeeklyOrder
from app.schemas.order import WeeklyOrderCreate, WeeklyOrderResponse
from app.utils.auth import get_current_user

router = APIRouter(tags=["Orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/orders/week", response_model=WeeklyOrderResponse)
def create_weekly_order(order: WeeklyOrderCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_order = WeeklyOrder(
        user_id=current_user["id"],
        week=order.week,
        meal=order.meal,
        date=order.date
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/orders/week", response_model=list[WeeklyOrderResponse])
def get_user_weekly_orders(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    orders = db.query(WeeklyOrder).filter(WeeklyOrder.user_id == current_user["id"]).all()
    return orders
