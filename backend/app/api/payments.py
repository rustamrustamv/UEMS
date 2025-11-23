"""
Payment processing with Stripe integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import stripe
import logging

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.models.payment import Payment, PaymentHistory, PaymentStatus, PaymentType
from app.schemas.payment import (
    PaymentCreate, PaymentResponse, PaymentIntentResponse,
    PaymentHistoryResponse, RefundRequest
)
from app.instrumentation.metrics import (
    payment_processing_duration, payments_total, payments_amount_total,
    stripe_webhook_events_total
)

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_API_KEY


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    user_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List payments. Students see their own, Admin sees all.
    """
    query = select(Payment)

    if current_user.role.value == "student":
        query = query.where(Payment.user_id == current_user.id)
    elif user_id and current_user.role.value == "admin":
        query = query.where(Payment.user_id == user_id)

    query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())

    result = await db.execute(query)
    payments = result.scalars().all()

    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment details.
    """
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Authorization check
    if current_user.role.value == "student" and str(payment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return payment


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe PaymentIntent for processing payment.
    """
    with payment_processing_duration.time():
        # Validate payment type
        if payment_data.payment_type not in [pt.value for pt in PaymentType]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment type. Must be one of: {', '.join([pt.value for pt in PaymentType])}"
            )

        # Create payment record in database
        new_payment = Payment(
            user_id=current_user.id,
            amount=payment_data.amount,
            status=PaymentStatus.PENDING,
            payment_type=PaymentType(payment_data.payment_type),
            semester=payment_data.semester,
            year=payment_data.year,
            description=payment_data.description
        )

        db.add(new_payment)
        await db.commit()
        await db.refresh(new_payment)

        # Create Stripe PaymentIntent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(float(payment_data.amount) * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'payment_id': str(new_payment.id),
                    'user_id': str(current_user.id),
                    'payment_type': payment_data.payment_type
                }
            )

            # Update payment with Stripe intent ID
            new_payment.stripe_payment_intent_id = intent.id
            await db.commit()

            # Create history record
            history = PaymentHistory(
                payment_id=new_payment.id,
                status='pending',
                webhook_event_id=intent.id,
                notes='Payment intent created'
            )
            db.add(history)
            await db.commit()

            logger.info(
                "Payment intent created",
                extra={
                    'event': 'payment_intent_created',
                    'payment_id': str(new_payment.id),
                    'amount': float(payment_data.amount),
                    'stripe_intent_id': intent.id,
                    'user_id': str(current_user.id)
                }
            )

            return PaymentIntentResponse(
                client_secret=intent.client_secret,
                payment_id=new_payment.id
            )

        except stripe.error.StripeError as e:
            logger.error(
                "Stripe error creating payment intent",
                extra={
                    'event': 'stripe_error',
                    'error': str(e),
                    'payment_id': str(new_payment.id)
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing error: {str(e)}"
            )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle Stripe webhook events.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid webhook payload", extra={'event': 'webhook_error'})
        stripe_webhook_events_total.labels(event_type='unknown', status='failed').inc()
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature", extra={'event': 'webhook_error'})
        stripe_webhook_events_total.labels(event_type='unknown', status='failed').inc()
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event['type']

    if event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        await handle_payment_success(payment_intent, db)
        stripe_webhook_events_total.labels(event_type='payment_intent.succeeded', status='processed').inc()

    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        await handle_payment_failure(payment_intent, db)
        stripe_webhook_events_total.labels(event_type='payment_intent.payment_failed', status='processed').inc()

    else:
        logger.info(f"Unhandled webhook event: {event_type}", extra={'event': 'webhook_received'})
        stripe_webhook_events_total.labels(event_type=event_type, status='ignored').inc()

    return {"status": "success"}


async def handle_payment_success(payment_intent: dict, db: AsyncSession):
    """Update payment status to succeeded"""
    payment_id = payment_intent['metadata'].get('payment_id')

    if not payment_id:
        logger.error("Payment ID not found in webhook metadata", extra={'event': 'webhook_error'})
        return

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = PaymentStatus.SUCCEEDED
        payment.stripe_customer_id = payment_intent.get('customer')

        # Create history record
        history = PaymentHistory(
            payment_id=payment.id,
            status='succeeded',
            webhook_event_id=payment_intent['id'],
            webhook_data=payment_intent,
            notes='Payment succeeded via webhook'
        )
        db.add(history)
        await db.commit()

        # Update metrics
        payments_total.labels(status='succeeded', payment_type=payment.payment_type.value).inc()
        payments_amount_total.labels(payment_type=payment.payment_type.value).inc(float(payment.amount))

        logger.info(
            "Payment succeeded",
            extra={
                'event': 'payment_succeeded',
                'payment_id': payment_id,
                'amount': float(payment.amount)
            }
        )


async def handle_payment_failure(payment_intent: dict, db: AsyncSession):
    """Update payment status to failed"""
    payment_id = payment_intent['metadata'].get('payment_id')

    if not payment_id:
        logger.error("Payment ID not found in webhook metadata", extra={'event': 'webhook_error'})
        return

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = PaymentStatus.FAILED

        # Create history record
        history = PaymentHistory(
            payment_id=payment.id,
            status='failed',
            webhook_event_id=payment_intent['id'],
            webhook_data=payment_intent,
            notes=f"Payment failed: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}"
        )
        db.add(history)
        await db.commit()

        # Update metrics
        payments_total.labels(status='failed', payment_type=payment.payment_type.value).inc()

        logger.warning(
            "Payment failed",
            extra={
                'event': 'payment_failed',
                'payment_id': payment_id
            }
        )


@router.get("/{payment_id}/history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment status history.
    """
    # Verify payment exists and user has access
    payment_result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = payment_result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if current_user.role.value == "student" and str(payment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get history
    history_result = await db.execute(
        select(PaymentHistory)
        .where(PaymentHistory.payment_id == payment_id)
        .order_by(PaymentHistory.timestamp.desc())
    )
    history = history_result.scalars().all()

    return history


@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: str,
    refund_data: RefundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Initiate a refund (Admin only).
    """
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.status != PaymentStatus.SUCCEEDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund succeeded payments"
        )

    try:
        # Create Stripe refund
        refund = stripe.Refund.create(
            payment_intent=payment.stripe_payment_intent_id,
            reason=refund_data.reason or "requested_by_customer"
        )

        # Update payment status
        payment.status = PaymentStatus.REFUNDED

        # Create history record
        history = PaymentHistory(
            payment_id=payment.id,
            status='refunded',
            webhook_event_id=refund.id,
            notes=f"Refund initiated by admin. Reason: {refund_data.reason or 'N/A'}"
        )
        db.add(history)
        await db.commit()

        # Update metrics
        payments_total.labels(status='refunded', payment_type=payment.payment_type.value).inc()

        logger.info(
            "Payment refunded",
            extra={
                'event': 'payment_refunded',
                'payment_id': payment_id,
                'refunded_by': str(current_user.id)
            }
        )

        return {"status": "refund_initiated", "refund_id": refund.id}

    except stripe.error.StripeError as e:
        logger.error(
            "Stripe error during refund",
            extra={'event': 'refund_error', 'error': str(e), 'payment_id': payment_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund processing error: {str(e)}"
        )
