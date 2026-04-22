from .views import OrderHistoryListView
from django.urls import path

urlpatterns = [
    path('', OrderHistoryListView.as_view(), name='order-history'),
]