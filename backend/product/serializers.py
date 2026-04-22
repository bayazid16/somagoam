from rest_framework.fields import ReadOnlyField
from rest_framework import serializers
from .models import Product,Category
from reviews.serializers import ReviewSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields='__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name=serializers.ReadOnlyField(source='category.name')
    class Meta:
        model=Product
        fields=['id','name','price','category','category_name','slug','image','description']




class ProductDetailSerializer(serializers.ModelSerializer):
    
    reviews = ReviewSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 
            'stock', 'image', 'category_name', 'average_rating', 'reviews'
        ]