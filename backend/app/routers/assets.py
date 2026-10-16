from fastapi import APIRouter, Depends

from app.errors import AppError
from app.models import AssetType
from app.schemas import Asset
from app.services.price_service import PriceService, Quote, get_price_service

router = APIRouter(prefix="/api/assets", tags=["Market"])


def _to_schema(quote: Quote) -> Asset:
    return Asset(
        symbol=quote.asset.symbol,
        name=quote.asset.name,
        type=quote.asset.type,
        price=quote.price,
        updated_at=quote.updated_at,
    )


@router.get("", response_model=list[Asset])
def list_assets(type: AssetType | None = None, prices: PriceService = Depends(get_price_service)):
    return [_to_schema(q) for q in prices.get_all() if type is None or q.asset.type == type]


@router.get("/{symbol}", response_model=Asset)
def get_asset(symbol: str, prices: PriceService = Depends(get_price_service)):
    quote = prices.get(symbol)
    if quote is None:
        raise AppError(404, "ASSET_NOT_FOUND", f"Varlık bulunamadı: {symbol}")
    return _to_schema(quote)
