from django.contrib import admin
from django.utils.html import format_html
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price','slug', 'category', 'stock', 'display_image','description']
    readonly_fields = ['display_image']
    fields = ['name', 'price', 'slug', 'category', 'stock', 'image', 'display_image','description']
    prepopulated_fields = {"slug": ("name",)}

    def display_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url )
        return "No Image"
    
    display_image.short_description = 'Preview'

# Register your models here.
