from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from order.models import Order, OrderItem
from product.models import Product
from category.models import Category

User = get_user_model()

class OrderAndPaymentTests(APITestCase):

    def setUp(self):
    
        self.user = User.objects.create_user(email='safa@example.com', password='password123')
        
        
        self.other_user = User.objects.create_user(email='other@example.com', password='password456')
        
    
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        
    
        self.product = Product.objects.create(
            name="Laptop", 
            stock=10, 
            price=50000,
            category=self.category
        )
        
        
        self.order = Order.objects.create(
            user=self.user,
            total_price=50000,
            status="Pending",
            tran_id="TRAN12345"
        )
        
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )
        
        
        self.client.force_authenticate(user=self.user)

    def test_search_order_by_transaction_id_success(self):
        
    
        url = reverse('order_search', kwargs={'tran_id': 'TRAN12345'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transaction_id'], 'TRAN12345')

    def test_search_order_not_found(self):
    
        url = reverse('order_search', kwargs={'tran_id': 'INVALID_ID'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_order_unauthorized_user(self):

        
        self.client.force_authenticate(user=self.other_user)
        url = reverse('order_search', kwargs={'tran_id': 'TRAN12345'})
        response = self.client.get(url)
        
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_failure_restores_stock(self):
    
        initial_stock = self.product.stock
        url = reverse('payment-fail', kwargs={'order_id': self.order.id})
        
        response = self.client.post(url)
        
        self.product.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.order.status, "Failed")
        self.assertEqual(self.product.stock, initial_stock + self.order_item.quantity)