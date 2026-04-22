from rest_framework.test import APITestCase
from rest_framework import response, status
from django.urls import reverse
from django.contrib.auth import get_user_model
from product.models import Product
from category.models import Category
from cart.models import Cart, CartItem  # adjust import based on your project

User = get_user_model()

class CartAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='safa@example.com', password='password123')
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name="Electronics", slug="electronics")

        self.product = Product.objects.create(
            name="Test Phone",
            price=1000,
            stock=10,
            category=self.category,
        )

        self.url = reverse('cart-operation')

    def test_add_to_cart(self):
        data = {"product_id": self.product.id, "action": "add"}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the product is really added
        cart_item = CartItem.objects.filter(cart__user=self.user, product=self.product).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.quantity, 1)

    def test_add_same_item_twice(self):
        # Add first time
        self.client.post(self.url, {"product_id": self.product.id, "action": "add"}, format='json')
        # Add second time
        self.client.post(self.url, {"product_id": self.product.id, "action": "add"}, format='json')

        cart_item = CartItem.objects.get(cart__user=self.user, product=self.product)
        self.assertEqual(cart_item.quantity, 2)

    
    def test_remove_from_cart(self):
    # Add first
        self.client.post(self.url, {"product_id": self.product.id, "action": "add"}, format='json')

        # Remove (decrease)
        response = self.client.post(self.url, {"product_id": self.product.id, "action": "remove"}, format='json')

        self.assertEqual(response.status_code, 200)

        # Use filter().exists() for a cleaner check
        item_exists = CartItem.objects.filter(
            cart__user=self.user,
            product=self.product
        ).exists()

        self.assertFalse(item_exists, f"CartItem still exists in DB!")
    


    def test_invalid_product(self):
        response = self.client.post(self.url, {"product_id": 99999, "action": "add"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Cart, CartItem
from product.models import Product, Category
from order.models import Order, OrderItem


class CheckOutAPITest(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name="Electronics")

        self.product = Product.objects.create(
            name="Laptop",
            price=50000,
            stock=10,
            category=self.category
        )

        self.cart = Cart.objects.create(user=self.user)

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

        self.url = "/api/cart/checkout/"

    
    
    def test_checkout_success(self):
        response = self.client.post(self.url, {
        "address": "Dhaka, Bangladesh"
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        order = Order.objects.first()

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_price, 100000)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        self.assertFalse(self.cart.items.exists())


    def test_checkout_without_address(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)




    def test_checkout_empty_cart(self):
        self.cart.items.all().delete()

        response = self.client.post(self.url, {
            "address": "Dhaka"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Your cart is empty")

    def test_checkout_insufficient_stock(self):
        self.product.stock = 1
        self.product.save()

        response = self.client.post(self.url, {
            "address": "Dhaka"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

        self.assertEqual(Order.objects.count(), 0)




    def test_order_expiry_time(self):
        response = self.client.post(self.url, {
            "address": "Dhaka"
        })

        order = Order.objects.first()

        order.refresh_from_db()

        expected = timezone.now() + timedelta(minutes=15)

        self.assertTrue(
            abs((order.expires_at - expected).total_seconds()) < 5
        )