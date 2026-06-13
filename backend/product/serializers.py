from rest_framework.fields import ReadOnlyField
from rest_framework import serializers
from .models import Product,Category
from reviews.serializers import ReviewSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields='__all__'

class SellerMiniSerializer(serializers.Serializer):
    """
    Small seller card shown in ProductDetail and product listings.
    Reads from sellers.Seller model via product.seller FK.
    """
    id           = serializers.IntegerField()
    slug         = serializers.CharField()
    company_name = serializers.CharField()
    logo         = serializers.ImageField()
    district     = serializers.CharField()
    rating       = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_products = serializers.IntegerField()
    total_sales    = serializers.IntegerField()
 

class ProductSerializer(serializers.ModelSerializer):
    category_name=serializers.ReadOnlyField(source='category.name')

    # Seller basic info for product cards
    seller_name = serializers.CharField(
        source='seller.company_name', read_only=True, default=None
    )
    seller_slug = serializers.CharField(
        source='seller.slug', read_only=True, default=None
    )
 
    class Meta:
        model=Product
        fields=['id','name','price','category','category_name','slug','image','description','seller_name','seller_slug']




class ProductDetailSerializer(serializers.ModelSerializer):
    
    reviews = ReviewSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

     # Full seller card info
    seller = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 
            'stock', 'image', 'category_name', 'average_rating', 'reviews'
        ]

    def get_seller(self, obj):
        if not obj.seller:
            return None
        s = obj.seller
        request = self.context.get('request')
        logo_url = None
        if s.logo:
            logo_url = request.build_absolute_uri(s.logo.url) if request else s.logo.url
 
        return {
            'id':             s.id,
            'slug':           s.slug,
            'company_name':   s.company_name,
            'logo':           logo_url,
            'district':       s.district,
            'division':       s.division,
            'tagline':        s.tagline,
            'rating':         str(s.rating),
            'total_products': s.total_products,
            'total_sales':    s.total_sales,
        }
 