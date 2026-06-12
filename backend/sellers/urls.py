from django.urls import path
from .views import (
    SellerRegisterView, SellerLoginView, SellerTokenRefreshView,
    SellerMeView, SellerDashboardView, SellerUploadView,
    SellerStatsView, SellerListView, SellerDetailView,
    SellerNotificationsView,
)
 
urlpatterns = [
    # Auth — completely separate from /api/auth/
    path('register/',       SellerRegisterView.as_view(),     name='seller-register'),
    path('login/',          SellerLoginView.as_view(),        name='seller-login'),
    path('token/refresh/',  SellerTokenRefreshView.as_view(), name='seller-token-refresh'),
    path('me/',             SellerMeView.as_view(),           name='seller-me'),
 
    # Dashboard
    path('dashboard/',      SellerDashboardView.as_view(),    name='seller-dashboard'),
    path('upload/',         SellerUploadView.as_view(),       name='seller-upload'),
    path('stats/',          SellerStatsView.as_view(),        name='seller-stats'),
    path('notifications/',  SellerNotificationsView.as_view(),name='seller-notifications'),
 
    # Public (for Producers page)
    path('',               SellerListView.as_view(),         name='sellers-list'),
    path('<slug:slug>/',   SellerDetailView.as_view(),       name='seller-detail'),
]