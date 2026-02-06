from sqlalchemy import Column, String, JSON, Enum as SQLEnum
from sqlalchemy.orm import declarative_base
from payments_service.app.core.models.merchant import MerchantStatus
import uuid

Base = declarative_base()

class MerchantModel(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    mcc = Column(String, nullable=False)
    country = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    tax_id = Column(String, nullable=False)
    status = Column(SQLEnum(MerchantStatus), default=MerchantStatus.ACTIVE)
    api_key = Column(String, unique=True, nullable=False)
    banking_info = Column(JSON, nullable=True)

class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    merchant_id = Column(String, nullable=False)
    amount = Column(JSON, nullable=False) # Store Amount object as JSON
    provider = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    # Add more fields as needed for the flow
