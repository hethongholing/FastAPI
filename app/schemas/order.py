from pydantic import BaseModel
from datetime import date

class WeeklyOrderBase(BaseModel):
    week: str  # Ví dụ: "2025-W27"
    meal: str
    date: date

class WeeklyOrderCreate(WeeklyOrderBase):
    pass

class WeeklyOrderResponse(WeeklyOrderBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
