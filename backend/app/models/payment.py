from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Numeric, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentType(str, enum.Enum):
    TUITION = "tuition"
    FEES = "fees"
    BOOKS = "books"
    OTHER = "other"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True)
    status = Column(SQLEnum(PaymentStatus), nullable=False, index=True)
    payment_type = Column(SQLEnum(PaymentType), nullable=False)
    semester = Column(String(20), nullable=True, index=True)
    year = Column(Integer, nullable=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payment_metadata = Column(JSONB, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
    )

    # Relationships
    user = relationship("User", back_populates="payments")
    history = relationship("PaymentHistory", back_populates="payment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Payment {self.id} - ${self.amount} ({self.status})>"


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    webhook_event_id = Column(String(255), nullable=True, index=True)
    webhook_data = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    payment = relationship("Payment", back_populates="history")

    def __repr__(self):
        return f"<PaymentHistory {self.payment_id} - {self.status}>"
