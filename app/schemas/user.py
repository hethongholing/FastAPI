from pydantic import BaseModel, EmailStr
from typing import Optional

# Đăng ký
class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    email: EmailStr
    phone: str
    role: str = "member"  # Mặc định member

# Đăng nhập
class UserLogin(BaseModel):
    username: str
    password: str

# Cập nhật thông tin
class UserUpdate(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    phone: str
    old_password: Optional[str] = None
    new_password: Optional[str] = None

# Schema trả về
class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    phone: str
    role: str
    avatar: Optional[str] = None  # ✅ Thêm trường avatar

    model_config = {
        "from_attributes": True
    }
