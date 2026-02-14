from pydantic import BaseModel, Field
from datetime import datetime, timezone
from payments_service.app.core.models.payment import PaymentProvider

class PrecalculatedRoute(BaseModel):
    subscription_id: str
    provider: PaymentProvider
    routing_decision: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PrecalculatedRouteCreate(BaseModel):
    subscription_id: str
    provider: PaymentProvider
    routing_decision: str
    expires_at: datetime
