# app/utils/permissions.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_role(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role is None:
            raise HTTPException(status_code=403, detail="Role not found")
        return role
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
