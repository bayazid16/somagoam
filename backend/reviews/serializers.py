from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    created_at = serializers.DateTimeField(format="%d %b %Y", read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True) # ✅ real name

    class Meta:
        model = Review
        fields = ['id', 'user','product', 'product_name', 'rating', 'comment', 'created_at']