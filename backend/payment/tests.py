"""
test_task.py — Full test suite for Celery tasks.

Run with:
    python manage.py test payment.tests.test_task
    # or with pytest:
    pytest payment/tests/test_task.py -v
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock, call

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core import mail

import datetime

from .models import BkashPayment
from .tasks import (
    send_order_confirmation_email,
    cancel_expired_orders,
    send_payment_failure_email,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_payment(order_id="ORDER-001", status=BkashPayment.Status.SUCCESS,
                 amount="500.00", payment_id="PID-001", trx_id="TRX-001"):
    """Create a BkashPayment test record."""
    return BkashPayment.objects.create(
        order_id=order_id,
        payment_id=payment_id,
        trx_id=trx_id,
        amount=Decimal(amount),
        status=status,
    )


def make_order(order_id, status="Pending", expires_at=None):
    """
    Create a mock Order object (not saved to DB).
    Replace with a real Order.objects.create() if your Order model is available.
    """
    order = MagicMock()
    order.id = order_id
    order.status = status
    order.expires_at = expires_at or (timezone.now() - datetime.timedelta(hours=1))
    order.items.all.return_value = []
    return order


# ══════════════════════════════════════════════════════════════════════════════
# Task 1 — send_order_confirmation_email
# ══════════════════════════════════════════════════════════════════════════════

class TestSendOrderConfirmationEmail(TestCase):

    # ── helpers ───────────────────────────────────────────────────────────────

    def _run(self, order_id="ORDER-001", email="user@test.com", name="Bayazid"):
        send_order_confirmation_email(order_id, email, name)

    # ── Test 1: Email sent with correct subject & recipient ───────────────────

    @patch("payment.tasks.render_to_string", return_value="<html>Success</html>")
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_sent_successfully(self, mock_render):
        make_payment(order_id="ORDER-001")

        self._run(order_id="ORDER-001", email="user@test.com", name="Bayazid")

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.subject, "Order Confirmation - #ORDER-001")
        self.assertIn("user@test.com", sent.to)
        self.assertEqual(sent.from_email, "noreply@somagom.com")


    # ── Test 2: Email body contains trx_id and amount ─────────────────────────

    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_body_contains_trx_and_amount(self, mock_render):
        make_payment(order_id="ORDER-002", trx_id="TRX-XYZ", amount="750.00")

        send_order_confirmation_email("ORDER-002", "u@test.com", "Rahim")

        sent = mail.outbox[0]
        self.assertIn("TRX-XYZ",  sent.body)
        self.assertIn("750.00",    sent.body)

    # ── Test 3: No BkashPayment record → falls back to N/A ───────────────────

    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_sent_even_without_payment_record(self, mock_render):
        # No BkashPayment created → should still send with N/A values
        self._run(order_id="ORDER-NONE", email="u@test.com", name="Karim")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("N/A", mail.outbox[0].body)

    # ── Test 4: render_to_string called with correct template & context ───────

    @patch("payment.tasks.send_mail")
    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    def test_correct_template_and_context_used(self, mock_render, mock_send):
        make_payment(order_id="ORDER-003", trx_id="TRX-003", amount="200.00",
                     payment_id="PID-003")

        send_order_confirmation_email("ORDER-003", "u@test.com", "Nadia")

        mock_render.assert_called_once()
        template_name, context = mock_render.call_args[0]
        self.assertEqual(template_name, "emails/order_success.html")
        self.assertEqual(context["order_id"], "ORDER-003")
        self.assertEqual(context["user_name"], "Nadia")
        self.assertEqual(context["trx_id"], "TRX-003")

    # ── Test 5: Exception is re-raised (so Celery can retry) ─────────────────

    @patch("payment.tasks.render_to_string", side_effect=Exception("Template missing"))
    def test_exception_is_reraised(self, mock_render):
        with self.assertRaises(Exception) as ctx:
            self._run()
        self.assertIn("Template missing", str(ctx.exception))

    # ── Test 6: Only SUCCESS payments are fetched, not FAILED ────────────────

    @patch("payment.tasks.send_mail")
    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    def test_only_success_payment_used(self, mock_render, mock_send):
        # FAILED record for same order — should be ignored
        make_payment(order_id="ORDER-004", status=BkashPayment.Status.FAILED,
                     trx_id="TRX-FAIL", payment_id="PID-FAIL")

        send_order_confirmation_email("ORDER-004", "u@test.com", "Sara")

        _, context = mock_render.call_args[0]
        # Should fall back to N/A since no SUCCESS record exists
        self.assertEqual(context["trx_id"], "N/A")


# ══════════════════════════════════════════════════════════════════════════════
# Task 2 — cancel_expired_orders
# ══════════════════════════════════════════════════════════════════════════════

class TestCancelExpiredOrders(TestCase):

    # ── Test 7: Expired order gets cancelled ─────────────────────────────────

    @patch("payment.tasks.Order")
    def test_expired_order_is_cancelled(self, MockOrder):
        order = make_order("10", status="Pending")
        MockOrder.objects.filter.return_value.prefetch_related.return_value \
            .exists.return_value = True
        MockOrder.objects.filter.return_value.prefetch_related \
            .return_value.__iter__ = lambda s: iter([order])

        cancel_expired_orders()

        self.assertEqual(order.status, "Cancelled")
        order.save.assert_called_once_with(update_fields=["status"])

    # ── Test 8: INITIATED bKash payment is cancelled ──────────────────────────

    @patch("payment.tasks.Order")
    def test_initiated_bkash_payment_cancelled(self, MockOrder):
        order = make_order("11", status="Pending")
        MockOrder.objects.filter.return_value.prefetch_related.return_value \
            .exists.return_value = True
        MockOrder.objects.filter.return_value.prefetch_related \
            .return_value.__iter__ = lambda s: iter([order])

        payment = make_payment(order_id="11",
                               status=BkashPayment.Status.INITIATED,
                               payment_id="PID-INIT-11")

        cancel_expired_orders()

        payment.refresh_from_db()
        self.assertEqual(payment.status, BkashPayment.Status.CANCELLED)

    # ── Test 9: SUCCESS bKash payment is NOT touched ──────────────────────────

    @patch("payment.tasks.Order")
    def test_success_payment_not_touched(self, MockOrder):
        order = make_order("12", status="Pending")
        MockOrder.objects.filter.return_value.prefetch_related.return_value \
            .exists.return_value = True
        MockOrder.objects.filter.return_value.prefetch_related \
            .return_value.__iter__ = lambda s: iter([order])

        payment = make_payment(order_id="12",
                               status=BkashPayment.Status.SUCCESS,
                               payment_id="PID-SUC-12")

        cancel_expired_orders()

        payment.refresh_from_db()
        self.assertEqual(payment.status, BkashPayment.Status.SUCCESS)

    # ── Test 10: Stock is restored correctly ──────────────────────────────────

    @patch("payment.tasks.Order")
    def test_stock_restored_for_each_item(self, MockOrder):
        product = MagicMock()
        product.stock = 5

        item = MagicMock()
        item.product  = product
        item.quantity = 3

        order = make_order("13")
        order.items.all.return_value = [item]

        MockOrder.objects.filter.return_value.prefetch_related.return_value \
            .exists.return_value = True
        MockOrder.objects.filter.return_value.prefetch_related \
            .return_value.__iter__ = lambda s: iter([order])

        cancel_expired_orders()

        self.assertEqual(product.stock, 8)  # 5 + 3
        product.save.assert_called_once_with(update_fields=["stock"])

    # ── Test 11: Multiple items — all stocks restored ─────────────────────────

    @patch("payment.tasks.Order")
    def test_multiple_items_all_stocks_restored(self, MockOrder):
        p1, p2 = MagicMock(stock=10), MagicMock(stock=20)
        i1, i2 = MagicMock(product=p1, quantity=2), MagicMock(product=p2, quantity=5)

        order = make_order("14")
        order.items.all.return_value = [i1, i2]

        MockOrder.objects.filter.return_value.prefetch_related.return_value \
            .exists.return_value = True
        MockOrder.objects.filter.return_value.prefetch_related \
            .return_value.__iter__ = lambda s: iter([order])

        cancel_expired_orders()

        self.assertEqual(p1.stock, 12)   # 10 + 2
        self.assertEqual(p2.stock, 25)   # 20 + 5

    # ── Test 12: No expired orders → returns early, no crash ─────────────────

    @patch("payment.tasks.Order")
    def test_no_expired_orders_does_nothing(self, MockOrder):
        MockOrder.objects.filter.return_value.prefetch_related.return_value \
            .exists.return_value = False

        # Should not raise
        result = cancel_expired_orders()
        self.assertIsNone(result)

    # ── Test 13: Non-expired Pending order is NOT cancelled ───────────────────

    @patch("payment.tasks.Order")
    def test_future_order_not_cancelled(self, MockOrder):
        """Orders expiring in the future must not be touched."""
        MockOrder.objects.filter.return_value.prefetch_related.return_value \
            .exists.return_value = False  # filter(expires_at__lt=now) returns nothing

        cancel_expired_orders()

        # Verify the filter included expires_at__lt (i.e. only past orders matched)
        call_kwargs = MockOrder.objects.filter.call_args[1]
        self.assertIn("expires_at__lt", call_kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# Task 3 — send_payment_failure_email
# ══════════════════════════════════════════════════════════════════════════════

class TestSendPaymentFailureEmail(TestCase):

    def _run(self, order_id="ORDER-F01", email="fail@test.com",
             name="Bayazid", reason="failure"):
        send_payment_failure_email(order_id, email, name, reason)

    # ── Test 14: Email sent with correct subject ──────────────────────────────

    @patch("payment.tasks.render_to_string", return_value="<html>Failed</html>")
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_failure_email_sent(self, mock_render):
        self._run()

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.subject, "Payment Failed - Order #ORDER-F01")
        self.assertIn("fail@test.com", sent.to)
        self.assertEqual(sent.from_email, "noreply@somagom.com")

    # ── Test 15: Cancel reason in email body ─────────────────────────────────

    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_cancel_reason_in_body(self, mock_render):
        self._run(reason="cancel")

        self.assertIn("cancel", mail.outbox[0].body)

    # ── Test 16: Correct template called ─────────────────────────────────────

    @patch("payment.tasks.send_mail")
    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    def test_failure_template_used(self, mock_render, mock_send):
        self._run(order_id="ORDER-F02", name="Karim", reason="failure")

        template_name, context = mock_render.call_args[0]
        self.assertEqual(template_name, "emails/payment_failed.html")
        self.assertEqual(context["order_id"],  "ORDER-F02")
        self.assertEqual(context["user_name"], "Karim")
        self.assertEqual(context["reason"],    "failure")

    # ── Test 17: Default reason is "unknown" ─────────────────────────────────

    @patch("payment.tasks.send_mail")
    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    def test_default_reason_is_unknown(self, mock_render, mock_send):
        send_payment_failure_email("ORDER-F03", "u@test.com", "Ali")

        _, context = mock_render.call_args[0]
        self.assertEqual(context["reason"], "unknown")

    # ── Test 18: Exception is re-raised ──────────────────────────────────────

    @patch("payment.tasks.render_to_string", side_effect=Exception("Template error"))
    def test_exception_reraised(self, mock_render):
        with self.assertRaises(Exception) as ctx:
            self._run()
        self.assertIn("Template error", str(ctx.exception))

    # ── Test 19: Both failure and cancel reasons handled ─────────────────────

    @patch("payment.tasks.send_mail")
    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    def test_failure_and_cancel_both_work(self, mock_render, mock_send):
        for reason in ("failure", "cancel"):
            send_payment_failure_email("ORDER-F04", "u@test.com", "User", reason)

        self.assertEqual(mock_send.call_count, 2)


# ══════════════════════════════════════════════════════════════════════════════
# Integration — Task chaining (confirm email after cancel_expired_orders)
# ══════════════════════════════════════════════════════════════════════════════

class TestTaskIntegration(TestCase):

    # ── Test 20: send_order_confirmation_email is a Celery tasks ──────────────

    def test_confirmation_email_is_shared_task(self):
        self.assertTrue(hasattr(send_order_confirmation_email, "delay"))
        self.assertTrue(hasattr(send_order_confirmation_email, "apply_async"))

    # ── Test 21: cancel_expired_orders is a Celery tasks ──────────────────────

    def test_cancel_expired_orders_is_shared_task(self):
        self.assertTrue(hasattr(cancel_expired_orders, "delay"))
        self.assertTrue(hasattr(cancel_expired_orders, "apply_async"))

    # ── Test 22: send_payment_failure_email is a Celery tasks ─────────────────

    def test_failure_email_is_shared_task(self):
        self.assertTrue(hasattr(send_payment_failure_email, "delay"))
        self.assertTrue(hasattr(send_payment_failure_email, "apply_async"))

    # ── Test 23: tasks can be called synchronously (CELERY_TASK_ALWAYS_EAGER) ─

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("payment.tasks.render_to_string", return_value="<html>ok</html>")
    @patch("payment.tasks.send_mail")
    def test_task_runs_synchronously_in_tests(self, mock_send, mock_render):
        make_payment(order_id="ORDER-EAGER")

        # .delay() runs synchronously due to CELERY_TASK_ALWAYS_EAGER
        send_order_confirmation_email.delay(
            "ORDER-EAGER", "u@test.com", "Bayazid"
        )

        mock_send.assert_called_once()