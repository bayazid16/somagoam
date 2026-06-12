"""
from django.contrib import admin
from django.utils import timezone
from .models import Seller, SellerNotification
 
 
@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display   = ['company_name', 'full_name', 'email', 'district', 'status', 'created_at']
    list_filter    = ['status', 'business_type', 'division', 'district']
    search_fields  = ['company_name', 'email', 'full_name', 'phone']
    readonly_fields = ['slug', 'total_products', 'total_sales', 'total_revenue',
                       'created_at', 'updated_at']
 
    fieldsets = (
        ('Login', {'fields': ('email', 'password', 'is_active')}),
        ('Personal', {'fields': ('full_name', 'phone', 'nid_number', 'nid_image', 'profile_pic')}),
        ('Business', {'fields': ('company_name', 'slug', 'business_type', 'trade_license',
                                  'trade_license_image', 'tin_number', 'business_phone',
                                  'website', 'tagline', 'bio', 'logo', 'banner', 'category')}),
        ('Address', {'fields': ('division', 'district', 'upazila', 'full_address')}),
        ('Bank / Payment', {'fields': ('bank_name', 'bank_account_no', 'bank_account_name',
                                        'bank_branch', 'bkash_number', 'nagad_number')}),
        ('Approval', {'fields': ('status', 'rejection_note', 'approved_at', 'approved_by')}),
        ('Stats', {'fields': ('total_products', 'total_sales', 'total_revenue', 'rating')}),
    )
 
    actions = ['approve_sellers', 'reject_sellers', 'ban_sellers']
 
    def approve_sellers(self, request, queryset):
        queryset.update(
            status=Seller.Status.APPROVED,
            approved_at=timezone.now(),
            approved_by=request.user.email,
        )
        # TODO: send approval email
    approve_sellers.short_description = "✅ Approve selected sellers"
 
    def reject_sellers(self, request, queryset):
        queryset.update(status=Seller.Status.REJECTED)
    reject_sellers.short_description = "❌ Reject selected sellers"
 
    def ban_sellers(self, request, queryset):
        queryset.update(status=Seller.Status.BANNED, is_active=False)
    ban_sellers.short_description = "🚫 Ban selected sellers"
 
 
@admin.register(SellerNotification)
class SellerNotificationAdmin(admin.ModelAdmin):
    list_display = ['seller', 'title', 'is_read', 'created_at']
"""