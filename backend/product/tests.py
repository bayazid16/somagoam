from django.test import TestCase
from .models import Product
from category.models import Category

class ModelTesting(TestCase):
    def setUp(self):
        #create test data
        self.category=Category.objects.create(
            name='Fashion',
            slug='fashion'
        )
        self.product=Product.objects.create(
            category=self.category,
            name='Jamdani',
            slug='jamdani',
            price=10000,
            stock=10,
            is_available=True


        )
    def test_category_model_entry(self):
        #is category model save data correctly?
        data=self.category
        self.assertTrue(isinstance(data,Category))
        self.assertEqual(str(data),'Fashion')
    
    def test_product_model_entry(self):
        #is product model save data correctly?
        data=self.product
        self.assertTrue(isinstance(data,Product))
        self.assertEqual(str(data),'Jamdani')
        self.assertEqual(data.price,10000)

    def test_product_category_relationship(self):
        #check category and product relationship
        self.assertEqual(self.product.category.name,'Fashion')




# Create your tests here.
