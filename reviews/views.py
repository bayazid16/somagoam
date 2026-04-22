from django.shortcuts import render
from prompt_toolkit.validation import ValidationError
from rest_framework import permissions
from order.models import Order
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Review
from .serializers import ReviewSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class IsVerifiedBuyer(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        product_id = request.data.get('product')
        if not product_id :
            return False
        has_bought=Order.objects.filter(
            user=request.user, 
            status='Paid', 
            items__product_id=product_id 
        ).exists()
        return has_bought
    






class ReviewCreateListView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsVerifiedBuyer]
    parsers = [MultiPartParser, FormParser, JSONParser] 

    def get_queryset(self):
        """
        Filter reviews by product_id if provided
        and order by newest first.
        """
        queryset = Review.objects.select_related('product','user').order_by('-created_at')

        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    def perform_create(self, serializer):
        """
        Attach logged-in user automatically.
        """

        if Review.objects.filter(user=self.request.user, product=serializer.validated_data['product']).exists():
            raise ValidationError("You already reviewed this product.")
        
        serializer.save(user=self.request.user)



class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.select_related('product','user').all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def get_queryset(self):
        
        return Review.objects.filter(user=self.request.user)

# Create your views here.
