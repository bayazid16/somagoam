import os
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.shortcuts import redirect
from django.http import HttpResponse,JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from order.models import Order
from product.models import Product
from .utils import get_sslcommerz_payment_url, verify_sslcommerz_payment
from .task import send_order_confirmation_email

class InitiatePaymentView(APIView):

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'payment_init'
    def post(self, request):
        order_id = request.data.get('order_id')
        try:
            order = Order.objects.get(id=order_id, user=request.user)

            tran_id = f"ORDER_{order.id}_{uuid.uuid4().hex[:6]}"
            order.tran_id = tran_id
            order.save()


            url = get_sslcommerz_payment_url(order, request.user)
            
            return Response({'payment_url': url}) if url else Response({'error': 'Failed'}, status=400)
        except Order.DoesNotExist:
            return Response({'error': 'Not Found'}, status=404)

@csrf_exempt
def payment_success(request):
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173') # Vite runs on 5173 not 3000
    if request.method == 'POST':
        data = request.POST
        val_id = data.get('val_id')
        bank_tran_id = data.get('bank_tran_id')
        card_type = data.get('card_type')
        tran_id = data.get('tran_id')
        try:
            order_id = int(tran_id.split('_')[1])
        except (IndexError, AttributeError):
            return redirect(f'{FRONTEND_URL}/payment-fail')


        
        validation_response = verify_sslcommerz_payment(val_id)

        if validation_response:

            if validation_response.get('status') == 'VALID' or validation_response.get('status') == 'AUTHENTICATED':
                order = Order.objects.select_related('user').get(id=order_id)    
                order.status = 'Paid'
                order.tran_id = tran_id
                order.val_id = val_id
                order.bank_tran_id = bank_tran_id
                order.card_type = card_type
                order.save()
                
                return redirect(f'{FRONTEND_URL}/payment-success?id=' + tran_id)
            else:
                return JsonResponse({'error': 'Payment validation failed at SSLCommerz!'}, status=400)
        else:
            return JsonResponse({'error': 'Failed to connect to validation server!'}, status=500)
    
    return redirect(f'{FRONTEND_URL}/payment-fail')



@csrf_exempt
def sslcommerz_ipn(request):

    if request.method == 'POST':
        data = request.POST
        val_id = data.get('val_id')
        bank_tran_id = data.get('bank_tran_id')
        card_type = data.get('card_type')
        tran_id = data.get('tran_id')
        amount = data.get('amount')
        
        
        validation_response = verify_sslcommerz_payment(val_id)

        if validation_response and validation_response.get('status') in ['VALID', 'AUTHENTICATED']:


                        
            
            try:
                order_id = int(tran_id.split('_')[1])
                
                order = Order.objects.select_related('user').get(id=order_id)          
                
                
                if float(amount) >= float(order.total_price):
                    if order.status != 'Paid': 
                        order.status = 'Paid'
                        order.tran_id = tran_id

                        order.val_id = val_id
                        order.bank_tran_id = bank_tran_id
                        order.card_type = card_type
                        order.save()
                    send_order_confirmation_email.delay(
                        order.id, 
                        order.user.email, 
                        order.user.username
                    )
                    
                
                return HttpResponse("IPN Handled Successfully", status=200)
            except (Order.DoesNotExist, IndexError):
                return HttpResponse("Order Not Found", status=404)

    return HttpResponse("Invalid Request", status=400)




class OrderTransactionSearchView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, tran_id):
        try:
        
            order = Order.objects.get(tran_id=tran_id, user=request.user)
            
            data = {
                "order_id": order.id,
                "amount": order.total_price,
                "status": order.status,
                "date": order.created_at.strftime("%d %b %Y, %I:%M %p"),
                "address": order.address,
                "transaction_id": order.tran_id
            }
            return Response(data, status=200)
            
        except Order.DoesNotExist:
            return Response({"error": "No order found with this Transaction ID"}, status=404)




from django.db import transaction

class PaymentFailView(APIView):
    def post(self, request, order_id):
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id)

                for item in order.items.all():
                    product = Product.objects.select_for_update().get(
                        id=item.product.id
                    )
                    product.stock += item.quantity
                    product.save()

                order.status = "Failed"
                order.save()

            return Response({"message": "Stock restored"})

        except Exception as e:
            return Response({"error": str(e)}, status=500)
# Create your views here.
