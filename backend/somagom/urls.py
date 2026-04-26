"""somagom URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from order.views import OrderHistoryListView
from users.views import UserProfileView
from dj_rest_auth.registration.views import VerifyEmailView
from allauth.account.views import ConfirmEmailView  
from django.urls import path, re_path
from .views import LogoutView

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/admin_tools_stats/', include('admin_tools_stats.urls')),#new
    path('api/auth/',include('dj_rest_auth.urls')),#login,registration,profile
    path("api/accounts/", include("allauth.urls")),#new
    path('api/auth/registration/',include('dj_rest_auth.registration.urls')),

    #local apps
    path('api/cart/', include('cart.urls')),
    path('api/payment/', include('payment.urls')),
    path('api/products/', include('product.urls')),
    path('api/profile/', include('users.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/orders/', include('order.urls')),



    path('api/auth/logout/', LogoutView.as_view()),

    path('api/auth/registration/account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent'),
    re_path(r'^account-confirm-email/(?P<key>[-:\w]+)/$', ConfirmEmailView.as_view(), name='account_confirm_email'),

]

if settings.DEBUG:
    urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
