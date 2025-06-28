from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100))
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    hashed_password = Column(Text)
    role = Column(String(50))
    avatar = Column(Text, nullable=True)  # ✅ Thêm cột avatar
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
