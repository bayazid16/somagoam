from django.urls import path
from .views import (
    SellerRegisterView, SellerLoginView, SellerTokenRefreshView,
    SellerMeView, SellerDashboardView, SellerUploadView,
    SellerStatsView, SellerListView, SellerDetailView,
    SellerNotificationsView,
)
from .product_views import (
    SellerProductListView,
    SellerAddProductView,
    SellerMyProductsView,
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

     # Public
    path('<slug:slug>/products/', SellerProductListView.as_view(), name='seller-products'),
 
    # Private (seller dashboard)
    path('products/',             SellerMyProductsView.as_view(),  name='seller-my-products'),
    path('products/add/',         SellerAddProductView.as_view(),  name='seller-add-product'),
    path('products/<int:product_id>/', SellerMyProductsView.as_view(), name='seller-delete-product'),
]