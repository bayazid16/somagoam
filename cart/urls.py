from django.urls import path
from .views import CartOperationView, CheckOut

urlpatterns = [
    
    path('', CartOperationView.as_view(), name='cart-operation'),
    path('item/<int:pk>/', CartOperationView.as_view(), name='cart-item-delete'),
    path('checkout/', CheckOut.as_view(), name='checkout'),
]