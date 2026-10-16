"""API şemaları. Alan adları ve tipleri docs/openapi.yaml ile birebir aynı tutulur."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    field_validator,
)
from pydantic.alias_generators import to_camel

from app.models import AssetType, Side

# İçeride Decimal, JSON'da OpenAPI'deki gibi number.
Number = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RegisterRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def _bcrypt_limit(cls, value: str) -> str:
        # bcrypt 72 bayttan uzun şifreyi reddeder; Türkçe karakterler 2 bayt sayılır.
        if len(value.encode()) > 72:
            raise ValueError("Şifre en fazla 72 bayt olabilir.")
        return value


class LoginRequest(ApiModel):
    email: EmailStr
    password: str


class AuthResponse(ApiModel):
    token: str
    expires_in: int


class Asset(ApiModel):
    symbol: str
    name: str
    type: AssetType
    price: Number
    updated_at: datetime


class Holding(ApiModel):
    symbol: str
    type: AssetType
    quantity: Number
    average_cost: Number
    current_price: Number
    profit_loss: Number


class Portfolio(ApiModel):
    balance: Number
    holdings: list[Holding]
    total_value: Number
    total_profit_loss: Number


class TradeRequest(ApiModel):
    symbol: str = Field(min_length=1, max_length=20)
    side: Side
    quantity: Decimal = Field(gt=0, max_digits=24, decimal_places=8)


class Transaction(ApiModel):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[str, BeforeValidator(str)]
    symbol: str
    side: Side
    quantity: Number
    price: Number
    total: Number
    created_at: datetime
