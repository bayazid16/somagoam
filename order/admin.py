from django.contrib import admin
from django.contrib.admin import register
from .models import Order,OrderItem
from django.utils.html import format_html

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = ['id', 'user', 'tran_id', 'total_price', 'colored_status', 'created_at']
    
    
    list_filter = ['status', 'created_at']
    
    
    search_fields = ['tran_id', 'user__username', 'user__email']
    
    
    inlines = [OrderItemInline]
    
    
    readonly_fields = ['tran_id', 'val_id', 'bank_tran_id']

    
    def colored_status(self, obj):

        colors = {
            'Paid': 'green',
            'Pending': 'orange',
            'Failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<b style="color: {};">{}</b>', color, obj.status)
    
    colored_status.short_description = 'Payment Status'
    colored_status.admin_order_field = 'status'


# admin.site.register(Order)
# admin.site.register(OrderItem)

# Register your models here.
