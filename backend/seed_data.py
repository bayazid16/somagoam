import os
import django
import random
import uuid
from faker import Faker
from django.utils.text import slugify

# আপনার প্রজেক্টের নাম somagom হলে নিচের লাইনটি ঠিক আছে
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'somagom.settings') 
django.setup()

from product.models import Product
from category.models import Category 

fake = Faker()

def seed_products(n=200):
    # ক্যাটাগরি নিশ্চিত করা
    category, _ = Category.objects.get_or_create(name="General", defaults={'slug': 'general'})
    
    print(f"Starting to seed {n} products...")
    
    for i in range(n):
        title = fake.catch_phrase()
        # নাম থেকে স্লাগ তৈরি করা এবং শেষে র‍্যান্ডম স্ট্রিং যোগ করা যাতে ইউনিক হয়
        generated_slug = slugify(title) + "-" + str(uuid.uuid4())[:8]
        
        Product.objects.create(
            name=title,
            slug=generated_slug, # এই লাইনটিই আপনার আগের এরর সমাধান করবে
            description=fake.text(),
            price=random.uniform(500, 5000),
            stock=random.randint(5, 50),
            category=category
        )
        
        if (i + 1) % 50 == 0:
            print(f"Inserted {i + 1} products...")

    print(f"Done! {n} products seeded successfully.")

if __name__ == '__main__':
    seed_products(200)