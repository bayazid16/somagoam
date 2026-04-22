from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from order.models import Order
from django.utils import timezone



@shared_task
def send_order_confirmation_email(order_id, user_email, user_name):
    subject = f"Order Confirmation - #{order_id}"
    context = {'user_name': user_name, 'order_id': order_id}



    html_message = render_to_string('emails/order_success.html', context)
    plain_message = f"Hi {user_name}, your order #{order_id} was successful!"

    send_mail(
        subject,
        plain_message,
        'noreply@somagoam.com',
        [user_email],
        html_message=html_message,
        fail_silently=False,
    )







@shared_task
def cancel_expired_orders():
    expired_orders = Order.objects.filter(
        status="Pending",
        expires_at__lt=timezone.now()
    )

    for order in expired_orders:
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        order.status = "Cancelled"
        order.save()