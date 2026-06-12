"""
models.py  –  bKash Payment record model.
Add to your existing models.py or a dedicated payments/models.py.
"""

from django.db import models
from django.utils import timezone


class BkashPayment(models.Model):

    class Status(models.TextChoices):
        INITIATED  = "INITIATED",  "Initiated"
        SUCCESS    = "SUCCESS",    "Success"
        FAILED     = "FAILED",     "Failed"
        CANCELLED  = "CANCELLED",  "Cancelled"
        REFUNDED   = "REFUNDED",   "Refunded"

    # Link to your order – adjust to your own Order model
    order_id              = models.CharField(max_length=64, db_index=True)

    # bKash-returned fields
    payment_id            = models.CharField(max_length=128, unique=True, null=True, blank=True)
    trx_id                = models.CharField(max_length=128, null=True, blank=True)
    merchant_invoice_no   = models.CharField(max_length=128, null=True, blank=True)

    amount                = models.DecimalField(max_digits=12, decimal_places=2)
    currency              = models.CharField(max_length=10, default="BDT")

    status                = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INITIATED,
        db_index=True,
    )

    # Raw API responses for audit / debugging
    create_response       = models.JSONField(null=True, blank=True)
    execute_response      = models.JSONField(null=True, blank=True)

    created_at            = models.DateTimeField(default=timezone.now)
    updated_at            = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name        = "bKash Payment"
        verbose_name_plural = "bKash Payments"

    def __str__(self):
        return f"Order {self.order_id} | {self.status} | {self.amount} BDT"