from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import Portfolio
from app.security import get_current_user
from app.services.price_service import PriceService, get_price_service
from app.services.trade_service import build_portfolio

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("", response_model=Portfolio)
def get_portfolio(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    prices: PriceService = Depends(get_price_service),
):
    return build_portfolio(db, user, prices)
