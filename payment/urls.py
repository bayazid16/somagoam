from django.urls import path
from .views import PaymentFailView, sslcommerz_ipn,InitiatePaymentView,payment_success,OrderTransactionSearchView


urlpatterns = [
    path('initiate-payment/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/ipn/', sslcommerz_ipn, name='sslcommerz_ipn'),
    path('order/search/<str:tran_id>/', OrderTransactionSearchView.as_view(), name='order_search'),
    path('payment/fail/<int:order_id>/', PaymentFailView.as_view(), name='payment-fail'),
]
