from pydantic import BaseModel
from datetime import date

class MemberCreate(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    birth_date: date | None = None
    gender: str | None = None

class MemberResponse(MemberCreate):
    id: int
    join_date: date | None = None

    class Config:
        from_attributes = True
