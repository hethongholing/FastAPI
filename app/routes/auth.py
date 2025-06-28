from fastapi import APIRouter, Form, HTTPException, Depends, Body, Header, Request
from sqlalchemy.orm import Session
from pydantic import EmailStr
from app.db.database import SessionLocal
from app.models.user import User
from app.utils.sms import generate_otp, send_otp_email
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from starlette.responses import RedirectResponse
import time, hashlib, datetime, re, os
from dotenv import load_dotenv

router = APIRouter(tags=["Auth"])  # ❌ Bỏ prefix, dùng trong main.py


# ====== Load cấu hình từ .env ======
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
BASE_URL = os.getenv("BASE_URL") or "http://localhost:8000"  # Giá trị mặc định để tránh cảnh báo VSCode
if not SECRET_KEY:
    raise ValueError("❌ Chưa cấu hình SECRET_KEY trong file .env")

# ====== Khởi tạo OAuth cho Google và Facebook ======
# oauth = OAuth()
# oauth.register(
#     name='google',
#     client_id=os.getenv("GOOGLE_CLIENT_ID"),
#     client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
#     server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
#     client_kwargs={"scope": "openid email profile"},
# )
# oauth.register(
#     name='facebook',
#     client_id=os.getenv("FACEBOOK_CLIENT_ID"),
#     client_secret=os.getenv("FACEBOOK_CLIENT_SECRET"),
#     access_token_url='https://graph.facebook.com/v10.0/oauth/access_token',
#     authorize_url='https://www.facebook.com/v10.0/dialog/oauth',
#     api_base_url='https://graph.facebook.com/v10.0/',
#     client_kwargs={'scope': 'email'},
# )

# ====== Lưu OTP & dữ liệu tạm ======
otp_store = {}                      # {email: (otp, timestamp)}
temp_user_data = {}                 # {email: user_info_dict}
forgot_password_otp_store = {}      # {email: (otp, timestamp)}

# ====== Hàm tạo token ======
def create_access_token(data: dict, expires_delta: int = 3600):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# ====== DB session ======
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ====== Hàm mã hoá mật khẩu ======
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# ====== Hàm đăng ký (Gửi OTP và lưu tạm thông tin) ======
@router.post("/register")
async def register_request(
    username: str = Form(...),
    password: str = Form(...),
    email: EmailStr = Form(...),
    full_name: str = Form(None),
    phone: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="❌ Tên đăng nhập đã tồn tại.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="❌ Email đã được sử dụng.")

    if len(password) < 8 or not re.search(r"[A-Z!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=400, detail="❌ Mật khẩu phải tối thiểu 8 ký tự và chứa ít nhất 1 ký tự in hoa hoặc ký tự đặc biệt.")

    if not re.fullmatch(r"0\d{9}", phone):
        raise HTTPException(status_code=400, detail="❌ Số điện thoại phải đủ 10 số và bắt đầu bằng số 0.")
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=400, detail="❌ Số điện thoại đã được sử dụng.")

    otp = generate_otp()
    otp_store[email] = (otp, time.time())
    await send_otp_email(email, otp, purpose="xác thực")

    temp_user_data[email] = {
        "username": username,
        "hashed_password": hash_password(password),
        "full_name": full_name,
        "phone": phone
    }

    return {"message": "✅ Đã gửi mã OTP đến email. Vui lòng xác thực để hoàn tất đăng ký."}

# ====== Hàm xác minh OTP và tạo tài khoản + trả token ======
@router.post("/verify-otp")
def verify_otp(email: EmailStr = Form(...), otp: str = Form(...), db: Session = Depends(get_db)):
    if email not in otp_store or email not in temp_user_data:
        raise HTTPException(status_code=400, detail="❌ Email chưa đăng ký hoặc chưa gửi OTP.")

    stored_otp, timestamp = otp_store[email]
    if time.time() - timestamp > 300:
        raise HTTPException(status_code=400, detail="❌ Mã OTP đã hết hạn.")
    if otp != stored_otp:
        raise HTTPException(status_code=400, detail="❌ Mã OTP không đúng.")

    data = temp_user_data[email]

    new_user = User(
        username=data["username"],
        email=email,
        hashed_password=data["hashed_password"],
        full_name=data["full_name"],
        phone=data["phone"],
        role="member"
    )
    db.add(new_user)
    db.commit()

    del otp_store[email]
    del temp_user_data[email]

    token = create_access_token({"sub": new_user.username, "role": new_user.role})

    return {
        "message": "✅ Đăng ký và xác minh OTP thành công!",
        "access_token": token,
        "token_type": "bearer"
    }

# ====== Hàm đăng nhập sinh token ======
@router.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.hashed_password != hash_password(password):
        raise HTTPException(status_code=401, detail="❌ Sai tên đăng nhập hoặc mật khẩu.")

    token = create_access_token({"sub": user.username, "role": user.role})

    return {
        "message": "✅ Đăng nhập thành công!",
        "access_token": token,
        "token_type": "bearer"
    }


# ====== Đăng nhập bằng Google ======
# @router.get("/login/google")
# async def login_google(request: Request):
#     redirect_uri = f"{BASE_URL}/auth/google/callback"
#     return await oauth.google.authorize_redirect(request, redirect_uri)


# @router.get("/google/callback")
# async def google_callback(request: Request, db: Session = Depends(get_db)):
#     """Xử lý callback từ Google, tạo tài khoản nếu chưa có"""
#     token = await oauth.google.authorize_access_token(request)
#     user_info = token.get("userinfo")
#     if not user_info:
#         raise HTTPException(status_code=400, detail="❌ Không lấy được thông tin từ Google.")

#     email = user_info['email']
#     full_name = user_info.get('name', "")
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         user = User(username=email.split('@')[0], email=email, hashed_password="", full_name=full_name, phone="", role="member")
#         db.add(user)
#         db.commit()

#     jwt_token = create_access_token({"sub": user.username, "role": user.role})
#     return {"access_token": jwt_token, "token_type": "bearer"}

# ====== Đăng nhập bằng Facebook ======
# @router.get("/login/facebook")
# async def login_facebook(request: Request):
#     """Chuyển hướng người dùng sang Facebook để xác thực"""
#     redirect_uri = f"{BASE_URL}/auth/facebook/callback"
#     return await oauth.facebook.authorize_redirect(request, redirect_uri)

# @router.get("/facebook/callback")
# async def facebook_callback(request: Request, db: Session = Depends(get_db)):
#     """Xử lý callback từ Facebook, tạo tài khoản nếu chưa có"""
#     token = await oauth.facebook.authorize_access_token(request)
#     resp = await oauth.facebook.get('me?fields=id,name,email', token=token)
#     user_info = resp.json()

#     email = user_info.get('email')
#     full_name = user_info.get('name', "")
#     if not email:
#         raise HTTPException(status_code=400, detail="❌ Facebook không cung cấp email.")

#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         user = User(username=email.split('@')[0], email=email, hashed_password="", full_name=full_name, phone="", role="member")
#         db.add(user)
#         db.commit()

#     jwt_token = create_access_token({"sub": user.username, "role": user.role})
#     return {"access_token": jwt_token, "token_type": "bearer"}



# ====== Hàm refresh token ======
@router.post("/refresh-token")
def refresh_token(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="❌ Token không hợp lệ hoặc đã hết hạn.")

    new_token = create_access_token({"sub": username, "role": role})

    return {
        "message": "✅ Đã cấp lại token mới!",
        "access_token": new_token,
        "token_type": "bearer"
    }

# ====== Hàm lấy thông tin người dùng ======
@router.get("/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="❌ Không tìm thấy người dùng.")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role
    }

# ====== Hàm gửi OTP khôi phục mật khẩu ======
@router.post("/forgot-password")
async def forgot_password(email: EmailStr = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="❌ Email chưa được đăng ký.")

    otp = generate_otp()
    forgot_password_otp_store[email] = (otp, time.time())
    await send_otp_email(email, otp, purpose="đổi mật khẩu")

    return {"message": "✅ Đã gửi mã OTP khôi phục mật khẩu đến email."}

# ====== Hàm xác minh OTP và đổi mật khẩu mới ======
@router.post("/reset-password")
def reset_password(
    email: EmailStr = Form(...),
    otp: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if email not in forgot_password_otp_store:
        raise HTTPException(status_code=400, detail="❌ Chưa gửi OTP hoặc OTP đã hết hạn.")

    stored_otp, timestamp = forgot_password_otp_store[email]
    if time.time() - timestamp > 300:
        raise HTTPException(status_code=400, detail="❌ Mã OTP đã hết hạn.")
    if otp != stored_otp:
        raise HTTPException(status_code=400, detail="❌ Mã OTP không đúng.")

    if len(new_password) < 8 or not re.search(r"[A-Z!@#$%^&*(),.?\":{}|<>]", new_password):
        raise HTTPException(status_code=400, detail="❌ Mật khẩu phải tối thiểu 8 ký tự và chứa ít nhất 1 ký tự in hoa hoặc ký tự đặc biệt.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="❌ Không tìm thấy người dùng.")

    user.hashed_password = hash_password(new_password)
    db.commit()

    del forgot_password_otp_store[email]

    return {"message": "✅ Đặt lại mật khẩu thành công."}

# ======  Hàm gửi lại mã OTP đăng ký: ======
@router.post("/resend-otp")
async def resend_otp(email: EmailStr = Form(...)):
    if email not in otp_store or email not in temp_user_data:
        raise HTTPException(status_code=400, detail="❌ Email chưa đăng ký hoặc chưa gửi OTP trước đó.")

    otp = generate_otp()
    otp_store[email] = (otp, time.time())
    await send_otp_email(email, otp, purpose="xác thực")

    return {"message": "✅ Đã gửi lại mã OTP xác thực tài khoản đến email."}

# ======  Hàm gửi lại OTP cho quên mật khẩu: ======
@router.post("/resend-otp-forgot-password")
async def resend_otp_forgot_password(email: EmailStr = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="❌ Email chưa được đăng ký.")

    if email not in forgot_password_otp_store:
        raise HTTPException(status_code=400, detail="❌ Chưa gửi OTP khôi phục mật khẩu trước đó.")

    otp = generate_otp()
    forgot_password_otp_store[email] = (otp, time.time())
    await send_otp_email(email, otp, purpose="đổi mật khẩu")

    return {"message": "✅ Đã gửi lại mã OTP khôi phục mật khẩu đến email."}

# ====== Xoá người dùng theo username ======
@router.delete("/users/by-usernames")
def delete_users_by_usernames(usernames: list[str] = Body(...), db: Session = Depends(get_db)):
    if not usernames:
        raise HTTPException(status_code=400, detail="❌ Danh sách username không được để trống.")

    deleted = []
    for username in usernames:
        user = db.query(User).filter(User.username == username).first()
        if user:
            db.delete(user)
            deleted.append(username)

    db.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="❌ Không tìm thấy người dùng nào khớp.")

    return {"message": f"✅ Đã xoá các user: {deleted}"}

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin người dùng.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username, "role": role}



