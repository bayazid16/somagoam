from datetime import timedelta
from django.utils import timezone

from django.db import models
from django.conf import settings 
from product.models import Product

import uuid



def get_expiry():
    return timezone.now() + timedelta(minutes=15)

class Order(models.Model):
    STATUS_CHOICES=[
        ('Pending','Pending'),
        ('Paid','Paid'),
        ('Shipped','Shipped'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled'),

    ]


    

    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    total_price=models.DecimalField(max_digits=10,decimal_places=2)
    #sslcommerz transaction and validation id
    tran_id = models.CharField(max_length=150,unique=True,blank=True,null=True,help_text="Merchant Transaction ID",db_index=True)
    val_id = models.CharField(max_length=150, blank=True, null=True, help_text="SSLCommerz Validation ID")
    


    #payment method (bkash,card)
    card_type = models.CharField(max_length=50, blank=True, null=True)
    bank_tran_id = models.CharField(max_length=150, blank=True, null=True)


    

    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')
    address=models.TextField()

    
    created_at=models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True,default=get_expiry)


    def __str__(self):
        return f"Order {self.id} by {self.user.email}"
    
    def save(self, *args, **kwargs):
        
        if not self.tran_id:
            
            self.tran_id = f"ORDER_{self.id}_{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    


class OrderItem(models.Model):
    order=models.ForeignKey(Order,related_name='items',on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"




# Create your models here.
