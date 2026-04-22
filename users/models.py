from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models



class UserManager(BaseUserManager):
    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError('The Email Field Must be set')
        email=self.normalize_email(email)
        user=self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self,email,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        return self.create_user(email,password,**extra_fields)

class User(AbstractUser):
    username=models.CharField(max_length=150,blank=True,null=True)
    email=models.EmailField(unique=True)

    #custom fields
    first_name=models.CharField(max_length=30,blank=True,null=True)
    last_name=models.CharField(max_length=30,blank=True,null=True)
    phone_number=models.CharField(max_length=15,blank=True,null=True)
    address=models.TextField(blank=True,null=True)
    date_joined=models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['username']

    objects=UserManager()

    def __str__(self):
        return self.email
    



    
    







 


