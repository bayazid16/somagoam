from .views import UserProfileView
from django.urls import path    



urlpatterns = [
    path('', UserProfileView.as_view(), name='user-profile'),
]