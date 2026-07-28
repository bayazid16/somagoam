"""
sellers/views.py
All seller API views — completely separate from the main user views.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Seller, SellerNotification
from .serializers import (
    SellerRegisterSerializer,
    SellerLoginSerializer,
    SellerPublicSerializer,
    SellerDashboardSerializer,
    get_seller_tokens,
)
from .authentication import SellerJWTAuthentication,IsSeller

logger = logging.getLogger(__name__)


# ─── 1. Seller Registration ───────────────────────────────────────────────────

class SellerRegisterView(APIView):
    """
    POST /api/seller/register/
    Creates a new seller account with status=pending.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SellerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        seller = serializer.save()
        tokens = get_seller_tokens(seller)

        # Notify admin (optional: send email)
        logger.info(f"New seller registration: {seller.email} | {seller.company_name}")

        return Response({
            "message": (
                "Registration successful! Your application is under review. "
                "We'll email you within 2-3 business days."
            ),
            "seller": SellerDashboardSerializer(seller).data,
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)


# ─── 2. Seller Login ─────────────────────────────────────────────────────────

class SellerLoginView(APIView):
    """
    POST /api/seller/login/
    Returns seller-specific JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SellerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        seller = serializer.validated_data['seller']
        tokens = get_seller_tokens(seller)

        status_messages = {
            'pending':  "Your account is under review. You'll be notified when approved.",
            'approved': f"Welcome back, {seller.company_name}!",
            'rejected': "Your application was rejected. Please contact support.",
            'banned':   "Your account has been suspended. Contact support.",
        }

        return Response({
            "seller":  SellerDashboardSerializer(seller).data,
            "tokens":  tokens,
            "message": status_messages.get(seller.status, ""),
        })


# ─── 3. Seller Token Refresh ─────────────────────────────────────────────────

class SellerTokenRefreshView(APIView):
    """POST /api/seller/token/refresh/"""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token required."}, status=400)
        try:
            token = RefreshToken(refresh_token)
            # Verify it's a seller token
            if token.get('type') != 'seller':
                return Response({"error": "Invalid token type."}, status=400)
            return Response({"access": str(token.access_token)})
        except TokenError as e:
            return Response({"error": str(e)}, status=401)


# ─── 4. Seller Me (current seller) ───────────────────────────────────────────

class SellerMeView(APIView):
    """GET /api/seller/me/"""
    authentication_classes = [SellerJWTAuthentication]
    permission_classes     = [IsSeller] 

    def get(self, request):
        return Response(SellerDashboardSerializer(request.seller).data)


# ─── 5. Seller Dashboard (update profile) ────────────────────────────────────

class SellerDashboardView(APIView):
    """
    GET  /api/seller/dashboard/   → get own profile
    PUT  /api/seller/dashboard/   → update own profile
    """
    authentication_classes = [SellerJWTAuthentication]
    permission_classes     = [IsSeller] 

    def get(self, request):
        return Response(SellerDashboardSerializer(request.seller).data)

    def put(self, request):
        serializer = SellerDashboardSerializer(
            request.seller, data=request.data,
            partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)


# ─── 6. Upload logo/banner/NID ───────────────────────────────────────────────

class SellerUploadView(APIView):
    """POST /api/seller/upload/"""
    authentication_classes = [SellerJWTAuthentication]
    permission_classes     = [IsSeller] 
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        seller    = request.seller
        file_type = request.data.get('type')  # logo | banner | nid | trade_license | profile_pic

        allowed = ['logo', 'banner', 'nid_image', 'trade_license_image', 'profile_pic']
        if file_type not in allowed:
            return Response({"error": f"type must be one of: {allowed}"}, status=400)

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided."}, status=400)

        setattr(seller, file_type, file)
        seller.save(update_fields=[file_type])

        return Response({
            "message": f"{file_type} uploaded successfully.",
            "url": request.build_absolute_uri(getattr(seller, file_type).url),
        })


# ─── 7. Seller Dashboard Stats ────────────────────────────────────────────────

class SellerStatsView(APIView):
    """GET /api/seller/stats/"""
    authentication_classes = [SellerJWTAuthentication]
    permission_classes     = [IsSeller] 

    def get(self, request):
        seller = request.seller

        # Replace with real queries when Product/Order models are connected
        # from products.models import Product
        # from order.models import Order
        # products = Product.objects.filter(seller=seller)
        # orders   = Order.objects.filter(seller=seller)

        return Response({
            "total_products":     seller.total_products,
            "total_sales":        seller.total_sales,
            "total_revenue":      str(seller.total_revenue),
            "rating":             str(seller.rating),
            "pending_orders":     0,
            "processing_orders":  0,
            "completed_orders":   0,
            "revenue_this_month": "0.00",
            "views_this_week":    0,
            "status":             seller.status,
        })


# ─── 8. Public Sellers List (Producers page) ─────────────────────────────────

class SellerListView(APIView):
    """GET /api/sellers/?district=cumilla&search=nakshi"""
    permission_classes = [AllowAny]

    def get(self, request):
        sellers  = Seller.objects.filter(status=Seller.Status.APPROVED, is_active=True)
        district = request.query_params.get('district')
        search   = request.query_params.get('search')

        if district:
            sellers = sellers.filter(district__icontains=district)
        if search:
            sellers = sellers.filter(company_name__icontains=search)

        return Response(SellerPublicSerializer(sellers, many=True,
                                               context={'request': request}).data)


# ─── 9. Public Seller Detail ─────────────────────────────────────────────────

class SellerDetailView(APIView):
    """GET /api/sellers/<slug>/"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        seller = get_object_or_404(Seller, slug=slug,
                                   status=Seller.Status.APPROVED, is_active=True)

        # products = Product.objects.filter(seller=seller, is_active=True)
        return Response({
            "seller":   SellerPublicSerializer(seller, context={'request': request}).data,
            "products": [],   # replace with real product data
        })


# ─── 10. Seller Notifications ────────────────────────────────────────────────

class SellerNotificationsView(APIView):
    """GET /api/seller/notifications/"""
    authentication_classes = [SellerJWTAuthentication]
    permission_classes     = [IsSeller] 

    def get(self, request):
        notes = SellerNotification.objects.filter(seller=request.seller)[:20]
        return Response([
            {"id": n.id, "title": n.title, "message": n.message,
             "is_read": n.is_read, "created_at": n.created_at}
            for n in notes
        ])

    def post(self, request):
        """Mark all as read."""
        SellerNotification.objects.filter(
            seller=request.seller, is_read=False
        ).update(is_read=True)
        return Response({"message": "All notifications marked as read."})