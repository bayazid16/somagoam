from django.db import models
from django.conf import settings
from product.models import Product


class Cart(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='cart')
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)

    class  Meta:
        indexes=[
            models.Index(fields=['cart','product']),
        ]#it can increse the performance of query when we want to find a specific product in a cart

    @property
    def subtotal(self):
        return self.product.price * self.quantity
    def __str__(self):
        return f"{self.quantity} x {self.product.name }"

# Create your models here.
