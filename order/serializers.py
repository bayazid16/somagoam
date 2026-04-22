from rest_framework import serializers
from .models import Order

class OrderHistorySerializer(serializers.ModelSerializer):
    
    created_at = serializers.DateTimeField(format="%d %b %Y, %I:%M %p")

    class Meta:
        model = Order
        fields = ['id', 'tran_id', 'total_price', 'status', 'created_at', 'address']