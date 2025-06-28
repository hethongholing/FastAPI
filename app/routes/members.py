from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberResponse
from typing import List
from app.utils.permissions import get_current_user_role  # ✅ kiểm tra role

router = APIRouter()

# ✅ [GET] Lấy danh sách tất cả hội viên
@router.get("/members", response_model=List[MemberResponse])
def get_members(db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.id.asc()).all()
    return members

# ✅ [GET] Lấy hội viên theo ID
@router.get("/members/{member_id}", response_model=MemberResponse)
def get_member_by_id(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội viên")
    return member

# ✅ [POST] Tạo mới hội viên (chỉ admin)
@router.post("/members", response_model=MemberResponse)
def create_member(
    member: MemberCreate,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)  # ✅ check role
):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được tạo hội viên")

    existing = db.query(Member).filter(Member.email == member.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    db_member = Member(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

# ✅ [PUT] Cập nhật hội viên (chỉ admin)
@router.put("/members/{member_id}", response_model=MemberResponse)
def update_member(
    member_id: int,
    updated_data: MemberCreate,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được cập nhật")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội viên")

    existing = db.query(Member).filter(Member.email == updated_data.email, Member.id != member_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được sử dụng bởi hội viên khác")

    for key, value in updated_data.dict().items():
        setattr(member, key, value)

    db.commit()
    db.refresh(member)
    return member

# ✅ [DELETE] Xoá hội viên (chỉ admin)
@router.delete("/members/{member_id}", response_model=MemberResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được xoá hội viên")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội viên")

    db.delete(member)
    db.commit()
    return member
