from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.db.database import Base

class WeeklyOrder(Base):
    __tablename__ = "weekly_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    week = Column(String, index=True)  # Ví dụ: "2025-W27"
    meal = Column(String)  # Thông tin món ăn, có thể là JSON string
    date = Column(Date)  # Ngày cụ thể trong tuần
