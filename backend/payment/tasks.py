import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from order.models import Order
from .models import BkashPayment

logger = logging.getLogger(__name__)


# ─── 1. Order Confirmation Email ─────────────────────────────────────────────

@shared_task
def send_order_confirmation_email(order_id, user_email, user_name):
    """
    Send a confirmation email after a successful bKash payment.
    Called from BkashCallbackView when statusCode == "0000".

    Usage in views.py (inside BkashCallbackView, after SUCCESS):
        send_order_confirmation_email.delay(
            order_id=record.order_id,
            user_email=request.user.email,   # or pass email separately
            user_name=request.user.get_full_name(),
        )
    """
    try:
        # Fetch payment record to include trx_id in email
        payment = BkashPayment.objects.filter(
            order_id=order_id,
            status=BkashPayment.Status.SUCCESS,
        ).first()

        subject = f"Order Confirmation - #{order_id}"
        context = {
            'user_name':  user_name,
            'order_id':   order_id,
            'trx_id':     payment.trx_id   if payment else "N/A",
            'amount':     payment.amount   if payment else "N/A",
            'payment_id': payment.payment_id if payment else "N/A",
        }

        html_message  = render_to_string('emails/order_success.html', context)
        plain_message = (
            f"Hi {user_name}, your order #{order_id} was successful!\n"
            f"Transaction ID: {context['trx_id']}\n"
            f"Amount: {context['amount']} BDT"
        )

        send_mail(
            subject,
            plain_message,
            'noreply@somagom.com',
            [user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Order confirmation email sent → {user_email} (order #{order_id})")

    except Exception as e:
        logger.error(f"send_order_confirmation_email failed for order #{order_id}: {e}")
        raise  # Celery will retry if configured


# ─── 2. Cancel Expired Orders + Restore Stock ────────────────────────────────

@shared_task
def cancel_expired_orders():
    """
    Periodic task — cancel Pending orders past their expiry time.
    Also cancels any INITIATED bKash payments for those orders,
    and restores product stock.

    Schedule in settings.py (Celery Beat):
        CELERY_BEAT_SCHEDULE = {
            'cancel-expired-orders': {
                'task': 'your_app.tasks.cancel_expired_orders',
                'schedule': crontab(minute='*/5'),  # every 5 minutes
            },
        }
    """
    now = timezone.now()

    expired_orders = Order.objects.filter(
        status="Pending",
        expires_at__lt=now,
    ).prefetch_related('items__product')

    if not expired_orders.exists():
        logger.info("cancel_expired_orders: no expired orders found.")
        return

    cancelled_count = 0

    for order in expired_orders:

        # ── Restore product stock ─────────────────────────────────────────────
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=["stock"])

        # ── Cancel the order ──────────────────────────────────────────────────
        order.status = "Cancelled"
        order.save(update_fields=["status"])

        # ── Mark any INITIATED bKash payment as CANCELLED ─────────────────────
        BkashPayment.objects.filter(
            order_id=str(order.id),
            status=BkashPayment.Status.INITIATED,
        ).update(status=BkashPayment.Status.CANCELLED)

        cancelled_count += 1
        logger.info(f"Order #{order.id} cancelled (expired at {order.expires_at})")

    logger.info(f"cancel_expired_orders: {cancelled_count} order(s) cancelled.")


# ─── 3. Payment Failure Notification Email (bonus) ───────────────────────────

@shared_task
def send_payment_failure_email(order_id, user_email, user_name, reason="unknown"):
    """
    Notify user when bKash payment fails or is cancelled.
    Called from BkashCallbackView on failure/cancel.

    Usage in views.py:
        send_payment_failure_email.delay(
            order_id=record.order_id,
            user_email=...,
            user_name=...,
            reason=callback_status,
        )
    """
    try:
        subject = f"Payment Failed - Order #{order_id}"
        context = {
            'user_name': user_name,
            'order_id':  order_id,
            'reason':    reason,
        }

        html_message  = render_to_string('emails/payment_failed.html', context)
        plain_message = (
            f"Hi {user_name}, your payment for order #{order_id} was not completed.\n"
            f"Reason: {reason}\n"
            f"Please try again or contact support."
        )

        send_mail(
            subject,
            plain_message,
            'noreply@somagom.com',
            [user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Payment failure email sent → {user_email} (order #{order_id})")

    except Exception as e:
        logger.error(f"send_payment_failure_email failed for order #{order_id}: {e}")
        raise