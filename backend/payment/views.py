"""
views.py  –  bKash payment views (DRF-based).

URL patterns to add in urls.py:
    path("api/bkash/create/",    BkashCreatePaymentView.as_view(), name="bkash-create"),
    path("api/bkash/callback/",  BkashCallbackView.as_view(),      name="bkash-callback"),
    path("api/bkash/refund/",    BkashRefundView.as_view(),        name="bkash-refund"),
"""

import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAdminUser,
)
from rest_framework import status

from .bkash_service import BkashService
from .models import BkashPayment
from django.db import transaction
from order.models import Order

logger = logging.getLogger(__name__)
bkash = BkashService()


# ─── 1. Create Payment ───────────────────────────────────────────────────────

class BkashCreatePaymentView(APIView):
    """
    POST /api/bkash/create/
    Body: { "order_id": "123" }

    Amount is intentionally NOT accepted from the client — it's read from
    the Order record itself, so a user can never pay less (or for someone
    else's order) than what's actually owed.

    Returns: { "bkashURL": "...", "payment_id": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response(
                {"error": "order_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Adjust this to whatever field/logic marks your Order as already paid
        if getattr(order, "is_paid", False):
            return Response(
                {"error": "This order has already been paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = order.total_price  # server-side truth, never client input

        callback_url = request.build_absolute_uri("/api/bkash/callback/")

        try:
            result = bkash.create_payment(
                amount=amount,
                order_id=order_id,
                callback_url=callback_url,
            )
        except Exception as e:
            logger.error(f"bKash create_payment error: {e}")
            return Response(
                {"error": "Failed to initiate bKash payment."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # NOTE: create_payment() already raises on any statusCode != "0000",
        # so if we reach here the call succeeded — no need to re-check it.

        BkashPayment.objects.create(
            order_id=order_id,
            payment_id=result.get("paymentID"),
            merchant_invoice_no=result.get("merchantInvoiceNumber"),
            amount=amount,
            status=BkashPayment.Status.INITIATED,
            create_response=result,
        )

        return Response({
            "bkashURL":   result["bkashURL"],
            "payment_id": result["paymentID"],
        })


# ─── 2. Callback (bKash redirects here after payment) ────────────────────────

class BkashCallbackView(APIView):
    """
    GET /api/bkash/callback/?paymentID=...&status=success|failure|cancel

    Never trust the `status` query param alone for a "success" outcome —
    it only tells us the user finished the bKash flow. We always confirm
    with execute_payment / query_payment server-to-server before marking
    anything as SUCCESS.
    """
    permission_classes = [AllowAny]

    FRONTEND_SUCCESS = getattr(settings, "BKASH_SUCCESS_URL", "http://localhost:3000/payment/success")
    FRONTEND_FAILURE = getattr(settings, "BKASH_FAILURE_URL", "http://localhost:3000/payment/failed")

    def get(self, request):
        payment_id      = request.GET.get("paymentID")
        callback_status = request.GET.get("status")

        if not payment_id:
            return redirect(self.FRONTEND_FAILURE)

        # Entire read-check-update flow stays inside ONE atomic block so the
        # row lock from select_for_update() is actually held while we act on it.
        with transaction.atomic():
            record = (
                BkashPayment.objects
                .select_for_update()
                .filter(payment_id=payment_id)
                .first()
            )

            # ── User cancelled or bKash reported failure ──────────────────
            if callback_status in ("failure", "cancel"):
                if record and record.status not in (
                    BkashPayment.Status.SUCCESS, BkashPayment.Status.REFUNDED
                ):
                    record.status = (
                        BkashPayment.Status.CANCELLED
                        if callback_status == "cancel"
                        else BkashPayment.Status.FAILED
                    )
                    record.save(update_fields=["status", "updated_at"])
                return redirect(f"{self.FRONTEND_FAILURE}?reason={callback_status}")

            if callback_status != "success":
                return redirect(self.FRONTEND_FAILURE)

            # ── Already processed — idempotent on bKash retrying the callback ──
            if record and record.status == BkashPayment.Status.SUCCESS:
                return redirect(
                    f"{self.FRONTEND_SUCCESS}"
                    f"?trxID={record.trx_id}"
                    f"&paymentID={record.payment_id}"
                    f"&amount={record.amount}"
                )

            # ── Verify with bKash server-to-server ─────────────────────────
            try:
                result = bkash.execute_payment(payment_id)
            except Exception as e:
                logger.error(f"bKash execute error, querying: {e}")
                try:
                    result = bkash.query_payment(payment_id)
                except Exception as qe:
                    logger.error(f"bKash query also failed: {qe}")
                    if record:
                        record.status = BkashPayment.Status.FAILED
                        record.save(update_fields=["status", "updated_at"])
                    return redirect(f"{self.FRONTEND_FAILURE}?reason=verification_failed")

            # Both execute_payment() and query_payment() raise on anything
            # other than statusCode "0000" — reaching this line means the
            # payment is genuinely confirmed successful.
            if record:
                record.status           = BkashPayment.Status.SUCCESS
                record.trx_id           = result.get("trxID")
                record.execute_response = result
                record.save(update_fields=["status", "trx_id", "execute_response", "updated_at"])

                # Adjust field name to match your Order model
                Order.objects.filter(id=record.order_id).update(is_paid=True)

            return redirect(
                f"{self.FRONTEND_SUCCESS}"
                f"?trxID={result.get('trxID')}"
                f"&paymentID={payment_id}"
                f"&amount={result.get('amount')}"
            )


# ─── 3. Refund ───────────────────────────────────────────────────────────────

class BkashRefundView(APIView):
    """
    POST /api/bkash/refund/
    Body: { "payment_id": "...", "amount": "100.00", "reason": "Customer request" }
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        payment_id = request.data.get("payment_id")
        raw_amount = request.data.get("amount")
        reason     = request.data.get("reason", "Refund")

        if not payment_id:
            return Response(
                {"error": "payment_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = None
        if raw_amount is not None:
            try:
                amount = Decimal(str(raw_amount))
                if amount <= 0:
                    raise InvalidOperation
            except (TypeError, InvalidOperation):
                return Response(
                    {"error": "Invalid refund amount."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        record = BkashPayment.objects.filter(
            payment_id=payment_id,
            status=BkashPayment.Status.SUCCESS,
        ).first()

        if not record:
            return Response(
                {"error": "No successful payment found for this payment_id."},
                status=status.HTTP_404_NOT_FOUND,
            )

        refund_amount = amount or record.amount
        if refund_amount > record.amount:
            return Response(
                {"error": "Refund amount cannot exceed the original payment amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = bkash.refund_transaction(
                payment_id=payment_id,
                trx_id=record.trx_id,
                amount=refund_amount,
                reason=reason,
            )
        except Exception as e:
            logger.error(f"bKash refund error: {e}")
            return Response(
                {"error": "Refund request failed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        record.status = BkashPayment.Status.REFUNDED
        record.save(update_fields=["status", "updated_at"])
        return Response({"message": "Refund successful.", "data": result})


# ─── 4. Payment Status check (for React polling) ─────────────────────────────

class BkashPaymentStatusView(APIView):
    """
    GET /api/bkash/status/<order_id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        record = BkashPayment.objects.filter(order_id=order_id).order_by("-created_at").first()
        if not record:
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "status":     record.status,
            "payment_id": record.payment_id,
            "trx_id":     record.trx_id,
            "amount":     str(record.amount),
        })


class OrderTransactionSearchView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, tran_id):
        try:
            order = Order.objects.get(tran_id=tran_id, user=request.user)

            data = {
                "order_id": order.id,
                "amount": order.total_price,
                "status": order.status,
                "date": order.created_at.strftime("%d %b %Y, %I:%M %p"),
                "address": order.address,
                "transaction_id": order.tran_id
            }
            return Response(data, status=200)

        except Order.DoesNotExist:
            return Response({"error": "No order found with this Transaction ID"}, status=404)