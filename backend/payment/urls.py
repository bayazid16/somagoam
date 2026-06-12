from django.urls import path
from .views import (OrderTransactionSearchView,BkashCreatePaymentView,BkashCallbackView, BkashRefundView,BkashPaymentStatusView,)


urlpatterns = [
    path('order/search/<str:tran_id>/', OrderTransactionSearchView.as_view(), name='order_search'),
    path("api/bkash/create/",           BkashCreatePaymentView.as_view(), name="bkash-create"),
    path("api/bkash/callback/",         BkashCallbackView.as_view(),      name="bkash-callback"),
    path("api/bkash/refund/",           BkashRefundView.as_view(),        name="bkash-refund"),
    path("api/bkash/status/<str:order_id>/", BkashPaymentStatusView.as_view(), name="bkash-status"),
]
    
