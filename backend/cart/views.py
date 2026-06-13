from datetime import timedelta
from django.utils import timezone
import logging
from venv import logger
from itertools import product
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart,CartItem
from product.models import Product
from django.db import transaction
from product.models import Product
from product.apps import ProductConfig
from order.models import Order,OrderItem
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import get_user_model





class CartOperationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        cart,created=Cart.objects.get_or_create(user=request.user)
        return Response({"total": cart.total_price})
    
    def post(self,request):
        product_id=request.data.get('product_id')
        action=request.data.get('action')
        cart,created=Cart.objects.get_or_create(user=request.user)
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response({"error": "Product not found"}, status=400)
        cart_item,created=CartItem.objects.get_or_create(cart=cart,product=product)

        if action == 'add':
            if created:
                cart_item.quantity = 1
                cart_item.save()
            else:

                if product.stock>cart_item.quantity:
                    cart_item.quantity+=1
                    cart_item.save()
                else:
                    return Response({"error":"Out of stock"},status=400)
            return Response({"message": "item add in cart"}, status=200)
        elif action == 'remove':
            cart_item = CartItem.objects.filter(cart=cart, product=product).first()
            if not cart_item:
                return Response({"error": "Item not in cart"}, status=400)

            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

            return Response({"message": "Removed from cart"}, status=200)
    def delete(self,request,pk):
        try:
            cart_item=CartItem.objects.get(id=pk)
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"error":"Item not found"},status=404)




logger = logging.getLogger(__name__)

class CheckOut(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        address        = request.data.get('address')
        payment_method = request.data.get('payment_method', 'cod')
 
        # ── Validation ────────────────────────────────────────────────────────
        if not address:
            return Response(
                {"error": "Shipping address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        # ── FIX: Accept cart items from frontend request ───────────────────────
        # Frontend sends: items = [{ product_id: 1, quantity: 2 }, ...]
        # This avoids relying on Django's Cart model being in sync
        frontend_items = request.data.get('items', [])
 
        try:
            with transaction.atomic():
                total_amount          = 0
                order_items_to_create = []
 
                # ── Option A: Use items sent from frontend ─────────────────────
                if frontend_items:
                    order = Order.objects.create(
                        user       = request.user,
                        address    = address,
                        total_price= 0,
                        status     = 'Pending',
                        expires_at = timezone.now() + timedelta(hours=24),
                    )
 
                    for item in frontend_items:
                        product_id = item.get('product_id') or item.get('id')
                        quantity   = int(item.get('quantity', item.get('qty', 1)))
 
                        product = Product.objects.select_for_update().get(id=product_id)
 
                        if product.stock < quantity:
                            raise ValueError(f"Sorry, '{product.name}' is out of stock.")
 
                        product.stock -= quantity
                        product.save()
 
                        order_items_to_create.append(
                            OrderItem(
                                order    = order,
                                product  = product,
                                price    = product.price,
                                quantity = quantity,
                            )
                        )
                        total_amount += product.price * quantity
 
                # ── Option B: Fallback — use Django Cart model ─────────────────
                else:
                    cart = Cart.objects.filter(
                        user=request.user
                    ).prefetch_related('items__product').first()
 
                    if not cart or not cart.items.exists():
                        return Response(
                            {"error": "Your cart is empty. Please add items before checkout."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
 
                    order = Order.objects.create(
                        user        = request.user,
                        address     = address,
                        total_price = 0,
                        status      = 'Pending',
                        expires_at  = timezone.now() + timedelta(hours=24),
                    )
 
                    for item in cart.items.all():
                        product = Product.objects.select_for_update().get(id=item.product.id)
 
                        if product.stock < item.quantity:
                            raise ValueError(f"Sorry, '{product.name}' is out of stock.")
 
                        product.stock -= item.quantity
                        product.save()
 
                        order_items_to_create.append(
                            OrderItem(
                                order    = order,
                                product  = product,
                                price    = product.price,
                                quantity = item.quantity,
                            )
                        )
                        total_amount += product.price * item.quantity
 
                    # Clear Django cart after order
                    cart.items.all().delete()
 
                # ── Save order items ───────────────────────────────────────────
                OrderItem.objects.bulk_create(order_items_to_create)
                order.total_price = total_amount
                order.save()
 
            logger.info(
                f"Order #{order.id} created for {request.user.email} "
                f"| method={payment_method} | total=৳{total_amount}"
            )
 
            return Response({
                "message":      "Order placed successfully!",
                "order_id":     order.id,
                "total_amount": str(total_amount),
                "status":       "Confirmed" if payment_method == 'cod' else "Pending Payment",
            }, status=status.HTTP_201_CREATED)
 
        except Product.DoesNotExist:
            return Response(
                {"error": "One or more products were not found."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Checkout Error for {request.user.email}: {str(e)}")
            return Response(
                {"error": "An internal error occurred. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 