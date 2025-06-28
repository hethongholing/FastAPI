from sqlalchemy import Column, Integer, String, Date
from app.db.database import Base

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True)
    phone = Column(String)
    birth_date = Column(Date)
    join_date = Column(Date)
    gender = Column(String)
