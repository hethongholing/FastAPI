from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  # ✅ Thêm dòng này
from dotenv import load_dotenv
from app.db.database import Base, engine
from app.routes import auth, members, orders, users
import os

load_dotenv()

app = FastAPI()

# ✅ Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Bắt buộc phải có SessionMiddleware cho OAuth
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# ✅ Tạo bảng DB nếu chưa có
Base.metadata.create_all(bind=engine)

# ✅ Route mặc định
@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}

# ✅ Import các router
app.include_router(members.router, tags=["Members"])
app.include_router(auth.router, prefix="/auth")
app.include_router(orders.router)
app.include_router(users.router)