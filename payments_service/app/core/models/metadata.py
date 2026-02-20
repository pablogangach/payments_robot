from pydantic import BaseModel
from typing import Optional

class CardBIN(BaseModel):
    bin: str
    brand: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    issuer: Optional[str] = None
    country: Optional[str] = None
    alpha_2: Optional[str] = None
    alpha_3: Optional[str] = None

class InterchangeFee(BaseModel):
    network: str
    card_type: str
    card_category: Optional[str] = None
    region: str
    fee_percent: float
    fee_fixed: float
