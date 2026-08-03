import os
from xml.parsers.expat import errors
from django.utils.text import slugify

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import AllowAny

from django.core.cache import cache
 
from .authentication import SellerJWTAuthentication,IsSeller
from .models import Seller

from product.models import Product,ProductImage
from product.serializers import ProductSerializer
from category.models import Category
                                                        
 
#1. Public: Get all products by a seller slug
 
class SellerProductListView(APIView):
    """
    GET /api/sellers/<slug>/products/
    Returns all products for a seller — used in SellerStore page.
    """
    permission_classes = [AllowAny]
 
    def get(self, request, slug):
        
        try:
            seller = Seller.objects.get(
                slug=slug, status=Seller.Status.APPROVED, is_active=True
            )
        except Seller.DoesNotExist:
            return Response({"error": "Seller not found."}, status=404)
 
        products = Product.objects.filter(
            seller=seller, is_available=True
        ).order_by('-created_at')
 
        # Optional category filter
        category = request.query_params.get('category')
        if category:
            products = products.filter(
                category__name__icontains=category
            )
 
        serializer = ProductSerializer(
            products, many=True, context={'request': request}
        )
 
        return Response({
            "seller": {
                "id":             seller.id,
                "slug":           seller.slug,
                "company_name":   seller.company_name,
                "tagline":        seller.tagline,
                "bio":            seller.bio,
                "logo":           request.build_absolute_uri(seller.logo.url) if seller.logo else None,
                "banner":         request.build_absolute_uri(seller.banner.url) if seller.banner else None,
                "district":       seller.district,
                "division":       seller.division,
                "rating":         str(seller.rating),
                "total_products": seller.total_products,
                "total_sales":    seller.total_sales,
                "category":       seller.category,
            },
            "products":      serializer.data,
            "total_count":   products.count(),
        })
 
 
# 2. Private: Seller posts a new product
 
class SellerAddProductView(APIView):
    """
    POST /api/seller/products/add/
    Seller dashboard — add a new product.
    Requires seller JWT token (Authorization: Bearer <seller_access_token>)
    """
    authentication_classes = [SellerJWTAuthentication]
    permission_classes     = [IsSeller] 
    parser_classes         = [MultiPartParser, FormParser]
 
    def post(self, request):
        seller = request.seller
 
        # Only approved sellers can post
        if not seller.is_approved:
            return Response(
                {"error": "Your account must be approved before listing products."},
                status=status.HTTP_403_FORBIDDEN,
            )
 
        
        
 
        # Required fields
        name        = request.data.get('name', '').strip()
        price       = request.data.get('price')
        category_id = request.data.get('category')
        description = request.data.get('description', '')
        stock       = request.data.get('stock', 0)
        images       = request.FILES.getlist('images')
 
        # Validation
        errors = {}
        if not name:        errors['name']     = 'Product name is required.'
        if not price:       errors['price']    = 'Price is required.'
        if not category_id: errors['category'] = 'Category is required.'
        if not images:       errors['image']    = 'Product image is required.'
        if not images:
            errors['images'] = 'At least one product image is required.'
        elif len(images) > 4:
            errors['images'] = 'You can upload a maximum of 4 images.'
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
 
        # Get category
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({"category": "Invalid category."}, status=400)
 
        # Auto-generate unique slug
        base_slug = slugify(name)
        slug, n   = base_slug, 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{n}"
            n += 1
 
        # Create product
        product = Product.objects.create(
            seller      = seller,
            category    = category,
            name        = name,
            slug        = slug,
            description = description,
            price       = price,
            stock       = stock,
            image       = images[0],
            is_available = True,
        )

        for i, img in enumerate(images):
            ProductImage.objects.create(product=product, image=img, order=i)
 
        # Update seller stats
        seller.total_products = Product.objects.filter(seller=seller).count()
        seller.save(update_fields=['total_products'])
 
        from product.serializers import ProductSerializer
        return Response(
            ProductSerializer(product, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
 
 
#3. Private: Seller's own product list
 
class SellerMyProductsView(APIView):
    """
    GET  /api/seller/products/      → seller's own product list
    DELETE /api/seller/products/<id>/  → delete a product
    """
    authentication_classes = [SellerJWTAuthentication]
    permission_classes     = [IsSeller] 
 
    def get(self, request):
        
        
 
        products = Product.objects.filter(
            seller=request.seller
        ).order_by('-created_at')
 
        serializer = ProductSerializer(
            products, many=True, context={'request': request}
        )
        return Response({
            "products":    serializer.data,
            "total_count": products.count(),
        })
 
    def delete(self, request, product_id):
        from product.models import Product
 
        try:
            product = Product.objects.get(id=product_id, seller=request.seller)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=404)
 
        product.delete()
 
        # Update seller stats
        request.seller.total_products = Product.objects.filter(
            seller=request.seller
        ).count()
        request.seller.save(update_fields=['total_products'])
        cache.clear()
 
        return Response({"message": "Product deleted."})
 