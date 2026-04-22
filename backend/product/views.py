from rest_framework import generics,filters
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PostgresFullTextSearchFilter
from .models import Product
from .serializers import ProductSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from .serializers import ProductDetailSerializer



class ProductListView(generics.ListAPIView):
    queryset=Product.objects.select_related('category').only(
            'id', 'name', 'price', 'category__name', 'image', 'created_at','description'
        ).order_by('-created_at') 
    serializer_class=ProductSerializer
    filter_backends=[DjangoFilterBackend,PostgresFullTextSearchFilter,filters.OrderingFilter]
    filterset_fields=['category']
    search_fields=['name','description']
    ordering_fields=['price','created_at']


    @method_decorator(cache_page(60 * 15))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    



    




class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all().select_related('category').prefetch_related('reviews')
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug' 

    def retrieve(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        cache_key = f'product_detail_{slug}'
        
        #
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        
        response = super().retrieve(request, *args, **kwargs)
        
        
        cache.set(cache_key, response.data, timeout=60*60)
        
        return response





