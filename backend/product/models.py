from django.db import models
from django.db.models import Avg
from category.models import Category
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from sellers.models import Seller




class Product(models.Model):
    category=models.ForeignKey(Category,related_name='products',on_delete=models.CASCADE)

    seller      = models.ForeignKey(
        Seller,               
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',           
    )
    name=models.CharField(max_length=255) #for search
    slug=models.SlugField(max_length=255,unique=True,db_index=True) #it has auto index
    description=models.TextField(blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    stock=models.IntegerField(default=0)
    is_available=models.BooleanField(default=True)
    image=models.ImageField(upload_to='products/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    #This field will store data for search.
    search_vector = SearchVectorField(null=True, blank=True)


    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.PositiveIntegerField(default=0)




    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) 
        
        
        
        Product.objects.filter(pk=self.pk).update(
            search_vector=SearchVector('name', weight='A') + SearchVector('description', weight='B')
        )
    



   

    class Meta:
        indexes=[
            models.Index(fields=['category', 'price']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']), 
            models.Index(fields=['seller']),
            GinIndex(fields=['search_vector']), #for full text search
        ]

    def __str__(self):
        return self.name




class ProductImage(models.Model):
    product    = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image      = models.ImageField(upload_to='products/gallery/')
    order      = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} — image {self.order + 1}"

# Create your models here.
