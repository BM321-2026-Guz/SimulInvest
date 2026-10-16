from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.errors import AppError
from app.models import User
from app.schemas import AuthResponse, LoginRequest, RegisterRequest
from app.security import create_access_token, hash_password, verify_password
from app.services.trade_service import create_wallet

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _token_response(user: User) -> AuthResponse:
    return AuthResponse(token=create_access_token(user.id), expires_in=settings.jwt_expires_seconds)


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalars(select(User).where(User.email == email)).first():
        raise AppError(409, "EMAIL_EXISTS", "Bu e-posta adresi zaten kayıtlı.")

    user = User(
        email=email, password_hash=hash_password(body.password), display_name=body.display_name
    )
    db.add(user)
    db.flush()  # user.id'yi al
    create_wallet(db, user)  # kullanıcı ve 100.000 TL cüzdan aynı transaction'da
    db.commit()
    return _token_response(user)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalars(select(User).where(User.email == body.email.lower())).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "E-posta veya şifre hatalı.")
    return _token_response(user)
