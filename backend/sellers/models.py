"""
sellers/models.py
Completely separate Seller model — no relation to the main User model.
Has its own password, token, and status system.

Django app: sellers
Add to INSTALLED_APPS: 'sellers'
"""

from django.db import models
from django.utils.text import slugify
from django.contrib.auth.hashers import make_password, check_password
import uuid


class Seller(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        BANNED   = 'banned',   'Banned'

    class BusinessType(models.TextChoices):
        INDIVIDUAL = 'individual', 'Individual / Sole Proprietor'
        COMPANY    = 'company',    'Registered Company'
        PARTNERSHIP = 'partnership', 'Partnership'

    # ── Login credentials ────────────────────────────────────────────────────
    email    = models.EmailField(unique=True, db_index=True)
    password = models.CharField(max_length=255)    # hashed
    is_active = models.BooleanField(default=True)

    # ── Personal Info ────────────────────────────────────────────────────────
    full_name   = models.CharField(max_length=200)
    phone       = models.CharField(max_length=20, unique=True)
    nid_number  = models.CharField(max_length=30, unique=True,
                                   help_text="National ID / Passport number")
    nid_image   = models.ImageField(upload_to='seller_nid/', null=True, blank=True)
    profile_pic = models.ImageField(upload_to='seller_pics/', null=True, blank=True)

    # ── Business Info ─────────────────────────────────────────────────────────
    company_name    = models.CharField(max_length=200)
    slug            = models.SlugField(max_length=220, unique=True, blank=True)
    business_type   = models.CharField(
        max_length=20, choices=BusinessType.choices,
        default=BusinessType.INDIVIDUAL,
    )
    trade_license   = models.CharField(max_length=100, null=True, blank=True,
                                        help_text="Trade license number")
    trade_license_image = models.ImageField(upload_to='seller_trade/', null=True, blank=True)
    tin_number      = models.CharField(max_length=50, null=True, blank=True,
                                        help_text="TIN / VAT number")
    business_phone  = models.CharField(max_length=20, null=True, blank=True)
    website         = models.URLField(null=True, blank=True)
    tagline         = models.CharField(max_length=300, null=True, blank=True)
    bio             = models.TextField(null=True, blank=True)
    logo            = models.ImageField(upload_to='seller_logos/', null=True, blank=True)
    banner          = models.ImageField(upload_to='seller_banners/', null=True, blank=True)
    category        = models.CharField(max_length=100, null=True, blank=True,
                                        help_text="Main product category")

    # ── Address ───────────────────────────────────────────────────────────────
    division        = models.CharField(max_length=100)
    district        = models.CharField(max_length=100)
    upazila         = models.CharField(max_length=100, null=True, blank=True)
    full_address    = models.TextField()

    # ── Bank / Payment Info ───────────────────────────────────────────────────
    bank_name       = models.CharField(max_length=100, null=True, blank=True)
    bank_account_no = models.CharField(max_length=50, null=True, blank=True)
    bank_account_name = models.CharField(max_length=200, null=True, blank=True)
    bank_branch     = models.CharField(max_length=100, null=True, blank=True)
    bkash_number    = models.CharField(max_length=20, null=True, blank=True)
    nagad_number    = models.CharField(max_length=20, null=True, blank=True)

    # ── Admin approval ────────────────────────────────────────────────────────
    status          = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.PENDING, db_index=True,
    )
    rejection_note  = models.TextField(null=True, blank=True)
    approved_at     = models.DateTimeField(null=True, blank=True)
    approved_by     = models.CharField(max_length=100, null=True, blank=True)

    # ── Stats ─────────────────────────────────────────────────────────────────
    total_products  = models.PositiveIntegerField(default=0)
    total_sales     = models.PositiveIntegerField(default=0)
    total_revenue   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    rating          = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = 'sellers'          # separate table name
        ordering    = ['-created_at']
        verbose_name = 'Seller'
        verbose_name_plural = 'Sellers'

    # ── Password helpers ──────────────────────────────────────────────────────
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # ── Slug auto-generate ────────────────────────────────────────────────────
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.company_name)
            slug, n = base, 1
            while Seller.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    def __str__(self):
        return f"{self.company_name} | {self.email} | {self.status}"


# ─── Seller Notification ─────────────────────────────────────────────────────

class SellerNotification(models.Model):
    seller  = models.ForeignKey(Seller, on_delete=models.CASCADE,
                                related_name='notifications')
    title   = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'seller_notifications'
        ordering = ['-created_at']