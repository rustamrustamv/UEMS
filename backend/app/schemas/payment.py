from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class PaymentBase(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_type: str
    semester: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_id: UUID


class PaymentResponse(PaymentBase):
    id: UUID
    user_id: UUID
    currency: str
    stripe_payment_intent_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentHistoryResponse(BaseModel):
    id: UUID
    payment_id: UUID
    status: str
    timestamp: datetime
    webhook_event_id: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class RefundRequest(BaseModel):
    reason: Optional[str] = None
