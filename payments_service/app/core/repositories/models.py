from sqlalchemy import Column, String, Float, JSON, Enum as SQLEnum, DateTime
from sqlalchemy.orm import declarative_base
from payments_service.app.core.models.merchant import MerchantStatus
from payments_service.app.core.models.payment import PaymentStatus, PaymentProvider
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class MerchantORM(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    mcc = Column(String, nullable=False)
    country = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    tax_id = Column(String, nullable=False)
    status = Column(String, default="active")
    api_key = Column(String, unique=True, default=lambda: f"pk_live_{uuid.uuid4().hex[:8]}")
    banking_info = Column(JSON, nullable=True)

class CustomerORM(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String, nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=True)
    payment_method_token = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PaymentORM(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String, nullable=False)
    customer_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    description = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    status = Column(String, default="pending")
    provider_payment_id = Column(String, nullable=True)
    routing_decision = Column(String, nullable=True)
    subscription_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class SubscriptionORM(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)
    merchant_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    next_renewal_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PrecalculatedRouteORM(Base):
    __tablename__ = "precalculated_routes"

    subscription_id = Column(String, primary_key=True)
    provider = Column(String, nullable=False)
    routing_decision = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class CardBINORM(Base):
    __tablename__ = "card_bins"

    bin = Column(String, primary_key=True)
    brand = Column(String, nullable=True)
    type = Column(String, nullable=True)
    category = Column(String, nullable=True)
    issuer = Column(String, nullable=True)
    country = Column(String, nullable=True)
    alpha_2 = Column(String, nullable=True)
    alpha_3 = Column(String, nullable=True)

class InterchangeFeeORM(Base):
    __tablename__ = "interchange_fees"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network = Column(String, nullable=False)
    card_type = Column(String, nullable=False)
    card_category = Column(String, nullable=True)
    region = Column(String, nullable=False)
    fee_percent = Column(Float, nullable=False)
    fee_fixed = Column(Float, nullable=False)
