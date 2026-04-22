from django.db import models
from django.conf import settings
from product.models import Product 
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=500)
    image = models.ImageField(upload_to='review_images/', blank=True, null=True)  # new
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"

# Create your models here.
