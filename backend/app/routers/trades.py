from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError
from app.models import Transaction as TransactionModel
from app.models import User
from app.schemas import TradeRequest, Transaction
from app.security import get_current_user
from app.services.price_service import PriceService, get_price_service
from app.services.trade_service import execute_trade

router = APIRouter(prefix="/api", tags=["Trade"])


@router.post("/trades", response_model=Transaction, status_code=201)
def create_trade(
    body: TradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    prices: PriceService = Depends(get_price_service),
):
    quote = prices.get(body.symbol)
    if quote is None:
        raise AppError(404, "ASSET_NOT_FOUND", f"Varlık bulunamadı: {body.symbol}")
    return execute_trade(db, user, quote, body.side, body.quantity)


@router.get("/transactions", response_model=list[Transaction])
def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(TransactionModel)
        .where(TransactionModel.user_id == user.id)
        .order_by(TransactionModel.created_at.desc(), TransactionModel.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all()
