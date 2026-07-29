from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product
from reviews.models import Review
from django.db.models import Avg, Count

@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    
    cache.delete_pattern('product_list_*')






@receiver([post_save, post_delete], sender=Review)
def update_product_rating(sender, instance, **kwargs):
    product = instance.product

    stats = Review.objects.filter(product=product).aggregate(
        avg=Avg("rating"),
        count=Count("id")
    )

    Product.objects.filter(id=product.id).update(
        average_rating=stats["avg"] or 0.00,
        review_count=stats["count"] or 0
    )