from django.urls import path
from .views import ReviewCreateListView, ReviewDetailView

urlpatterns = [
    
    
    path('', ReviewCreateListView.as_view(), name='review-list-create'),

    
    path('<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
]