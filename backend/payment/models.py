from django.db import models
from django.conf import settings
from order.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('cod','Cod'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS,null=True,blank=True)
    sender_number = models.CharField(max_length=15,null=True,blank=True) 
    transaction_id = models.CharField(max_length=50, unique=True,null=True,blank=True) 
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    is_verified = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.amount}"