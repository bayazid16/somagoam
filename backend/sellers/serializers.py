"""
sellers/serializers.py
Seller-specific serializers + custom JWT token generation
(completely separate from the main user JWT)
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Seller


# ─── Custom token for Seller (separate from User tokens) ─────────────────────

def get_seller_tokens(seller):
    """
    Generate JWT tokens for a Seller object.
    We attach seller_id and type='seller' to the payload
    so the backend can distinguish seller tokens from user tokens.
    """
    refresh = RefreshToken()
    refresh['seller_id'] = seller.id
    refresh['email']     = seller.email
    refresh['type']      = 'seller'        # ← distinguishes from user tokens

    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


# ─── Registration serializer ─────────────────────────────────────────────────

class SellerRegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = Seller
        fields = [
            # Step 1 — Personal
            'full_name', 'email', 'phone', 'nid_number',
            'password', 'confirm_password',
            # Step 2 — Business
            'company_name', 'business_type', 'trade_license',
            'tin_number', 'business_phone', 'category',
            # Step 3 — Address
            'division', 'district', 'upazila', 'full_address',
            # Step 4 — Payment
            'bank_name', 'bank_account_no', 'bank_account_name',
            'bank_branch', 'bkash_number', 'nagad_number',
        ]

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        seller = Seller(**validated_data)
        seller.set_password(raw_password)
        seller.save()
        return seller


# ─── Login serializer ────────────────────────────────────────────────────────

class SellerLoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data['email'].strip().lower()
        try:
            seller = Seller.objects.get(email=email)
        except Seller.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "No seller account found with this email."}
            )

        if not seller.check_password(data['password']):
            raise serializers.ValidationError(
                {"password": "Incorrect password."}
            )

        if not seller.is_active:
            raise serializers.ValidationError(
                {"error": "Your account has been deactivated."}
            )

        data['seller'] = seller
        return data


# ─── Public profile serializer ───────────────────────────────────────────────

class SellerPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Seller
        fields = [
            'id', 'slug', 'company_name', 'tagline', 'bio',
            'logo', 'banner', 'district', 'division',
            'website', 'category',
            'total_products', 'total_sales', 'rating',
        ]


# ─── Private (dashboard) serializer ──────────────────────────────────────────

class SellerDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Seller
        fields = [
            'id', 'slug', 'email', 'full_name', 'phone',
            'profile_pic', 'company_name', 'business_type',
            'trade_license', 'tin_number', 'business_phone',
            'website', 'tagline', 'bio', 'logo', 'banner', 'category',
            'division', 'district', 'upazila', 'full_address',
            'bank_name', 'bank_account_no', 'bank_account_name',
            'bank_branch', 'bkash_number', 'nagad_number',
            'status', 'rejection_note', 'approved_at',
            'total_products', 'total_sales', 'total_revenue', 'rating',
            'created_at',
        ]
        read_only_fields = [
            'slug', 'email', 'status', 'rejection_note',
            'approved_at', 'total_products', 'total_sales',
            'total_revenue', 'rating', 'created_at',
        ]