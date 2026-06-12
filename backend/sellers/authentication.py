"""
sellers/authentication.py
Custom JWT authentication class for Seller model.
Completely separate from Django's User authentication.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import Seller


class SellerJWTAuthentication(BaseAuthentication):
    """
    Custom authentication for Seller.
    Reads Bearer token from Authorization header,
    verifies it's a seller token (type='seller'),
    and attaches the Seller object to request.seller.

    Usage in views:
        authentication_classes = [SellerJWTAuthentication]
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return None

        raw_token = auth_header.split(' ')[1]

        try:
            token = AccessToken(raw_token)
        except TokenError:
            raise AuthenticationFailed("Invalid or expired token.")

        # Verify it's a seller token, not a user token
        if token.get('type') != 'seller':
            raise AuthenticationFailed("This endpoint requires a seller token.")

        seller_id = token.get('seller_id')
        if not seller_id:
            raise AuthenticationFailed("Invalid token payload.")

        try:
            seller = Seller.objects.get(id=seller_id, is_active=True)
        except Seller.DoesNotExist:
            raise AuthenticationFailed("Seller not found or deactivated.")

        # Attach seller to request — access via request.seller
        request.seller = seller

        # Return (None, None) because we're not using Django's User system
        return (None, None)

    def authenticate_header(self, request):
        return 'Bearer'