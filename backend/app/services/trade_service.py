"""Al-sat ve portföy iş mantığı (Story 1.2, 1.4)."""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import AppError
from app.models import AssetType, Holding, Side, Transaction, User, Wallet
from app.services.price_service import PriceService, Quote

CENT = Decimal("0.01")
QTY_STEP = Decimal("0.00000001")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def create_wallet(db: Session, user: User) -> Wallet:
    wallet = Wallet(user_id=user.id, balance=settings.initial_balance)
    db.add(wallet)
    return wallet


def _validate_quantity(quote: Quote, quantity: Decimal) -> None:
    if quote.asset.type == AssetType.STOCK and quantity != quantity.to_integral_value():
        raise AppError(400, "INVALID_QUANTITY", "Hisse senedi adedi tam sayı olmalıdır.")


def execute_trade(
    db: Session, user: User, quote: Quote, side: Side, quantity: Decimal
) -> Transaction:
    """Emri anlık fiyattan tek bir DB transaction içinde işler. Hata olursa hiçbir şey değişmez."""
    _validate_quantity(quote, quantity)
    total = money(quote.price * quantity)
    if total <= 0:
        raise AppError(400, "INVALID_QUANTITY", "İşlem tutarı 0,01 TL'den küçük olamaz.")

    wallet = db.scalars(select(Wallet).where(Wallet.user_id == user.id)).one()
    holding = db.scalars(
        select(Holding).where(Holding.user_id == user.id, Holding.symbol == quote.asset.symbol)
    ).one_or_none()
    balance = money(wallet.balance)

    if side == Side.BUY:
        if balance < total:
            raise AppError(400, "INSUFFICIENT_BALANCE", "Yetersiz bakiye.")
        wallet.balance = balance - total
        if holding is None:
            db.add(
                Holding(
                    user_id=user.id,
                    asset_type=quote.asset.type.value,
                    symbol=quote.asset.symbol,
                    quantity=quantity,
                    average_cost=quote.price,
                )
            )
        else:
            old_qty = holding.quantity
            new_qty = old_qty + quantity
            avg = (old_qty * holding.average_cost + quantity * quote.price) / new_qty
            holding.quantity = new_qty
            holding.average_cost = avg.quantize(QTY_STEP, rounding=ROUND_HALF_UP)
    else:
        owned = holding.quantity if holding else Decimal(0)
        if owned < quantity:
            raise AppError(400, "INSUFFICIENT_QUANTITY", "Sahip olunandan fazla adet satılamaz.")
        wallet.balance = balance + total
        remaining = owned - quantity
        if remaining == 0:
            db.delete(holding)
        else:
            holding.quantity = remaining  # satışta ortalama maliyet değişmez

    tx = Transaction(
        user_id=user.id,
        asset_type=quote.asset.type.value,
        symbol=quote.asset.symbol,
        side=side.value,
        quantity=quantity,
        price=quote.price,
        total=total,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def build_portfolio(db: Session, user: User, prices: PriceService) -> dict:
    wallet = db.scalars(select(Wallet).where(Wallet.user_id == user.id)).one()
    rows = db.scalars(
        select(Holding).where(Holding.user_id == user.id).order_by(Holding.symbol)
    ).all()

    balance = money(wallet.balance)
    holdings = []
    holdings_value = Decimal(0)
    for h in rows:
        quote = prices.get(h.symbol)
        current = quote.price if quote else h.average_cost
        value = current * h.quantity
        holdings_value += value
        holdings.append(
            {
                "symbol": h.symbol,
                "type": h.asset_type,
                "quantity": h.quantity,
                "average_cost": h.average_cost,
                "current_price": current,
                "profit_loss": money((current - h.average_cost) * h.quantity),
            }
        )

    total_value = money(balance + holdings_value)
    return {
        "balance": balance,
        "holdings": holdings,
        "total_value": total_value,
        "total_profit_loss": money(total_value - settings.initial_balance),
    }
