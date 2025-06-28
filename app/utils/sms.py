import random
import os
from email.message import EmailMessage
from aiosmtplib import SMTP
from dotenv import load_dotenv
from pathlib import Path

# ✅ Load .env đúng đường dẫn
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

print("✅ SMTP_USER =", SMTP_USER)
print("✅ SMTP_PASSWORD =", SMTP_PASSWORD)

# ====== Sinh mã OTP ======
def generate_otp():
    return str(random.randint(100000, 999999))

# ====== Hàm gửi email OTP linh hoạt theo mục đích ======
async def send_otp_email(email: str, otp: str, purpose: str = "xác thực"):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = email

    if purpose == "đổi mật khẩu":
        msg["Subject"] = "Mã OTP xác nhận đổi mật khẩu"
        msg.set_content(f"Mã OTP để đổi mật khẩu của bạn là: {otp}. Mã có hiệu lực trong 5 phút.")
    else:
        msg["Subject"] = "Mã OTP xác thực tài khoản"
        msg.set_content(f"Mã OTP để xác thực tài khoản của bạn là: {otp}. Mã có hiệu lực trong 5 phút.")

    smtp = SMTP(hostname="smtp.gmail.com", port=587, start_tls=True)
    await smtp.connect()
    await smtp.login(SMTP_USER, SMTP_PASSWORD)
    await smtp.send_message(msg)
    await smtp.quit()
