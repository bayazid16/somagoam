import requests
from django.conf import settings

def get_sslcommerz_payment_url(order, user):
    
    url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php" if settings.SSLCOMMERZ_IS_SANDBOX else "https://securepay.sslcommerz.com/gwprocess/v4/api.php"

    payload = {
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASS,
        'total_amount': float(order.total_price),
        'currency': 'BDT',
        'tran_id': order.tran_id,
        'success_url': "https://alina-drearies-heliacally.ngrok-free.dev/api/payment/payment/success/",
        'fail_url': "https://alina-drearies-heliacally.ngrok-free.dev/payment/fail/",
        'cancel_url': "https://alina-drearies-heliacally.ngrok-free.dev/payment/cancel/",
        'ipn_url': "https://alina-drearies-heliacally.ngrok-free.dev/api/payment/payment/ipn/",
        'cus_name': user.username,
        'cus_email': user.email,
        'cus_phone': '01700000000',
        'cus_add1': 'Dhaka', 'cus_city': 'Dhaka', 'cus_country': 'Bangladesh',
        'shipping_method': 'NO', 'product_name': 'Mixed Goods', 'product_category': 'General', 'product_profile': 'general',
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'SUCCESS':
            return data.get('GatewayPageURL')
        else:
            
            print("SSLCommerz Error Details:", data.get('failedreason'))
            return None
    except Exception as e:
        print(f"Error connecting to SSLCommerz: {e}")
        return None


def verify_sslcommerz_payment(val_id):
    
    url = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php" if settings.SSLCOMMERZ_IS_SANDBOX else "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"
    
    params = {
        'val_id': val_id,
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASS,
        'format': 'json'
    }
    try:
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
    
        if response.text:
            return response.json()
        else:
            print("SSLCommerz returned an empty response during validation.")
            return None

    except requests.exceptions.JSONDecodeError:
        
        print("Failed to decode JSON. SSLCommerz Response was:", response.text)
        return None
    except Exception as e:
        print("Validation Request Error:", str(e))
        return None