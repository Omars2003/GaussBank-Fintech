"""
URL configuration for gauss project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from accounts import views
from django.urls import path
from accounts import views
from accounts.views import CustomLoginView
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
 ########################################################
    path('group-savings/', views.group_savings_list, name='group_savings_list'),  # Página de lista
    path('group-savings/create/', views.group_savings_create, name='group_savings_create'),  # Crear grupo
    path('group-savings/<int:group_id>/', views.group_savings_detail, name='group_savings_detail'),  # Detalles de grupo
    path('savings-challenge/', views.savings_challenge, name='savings_challenge'),
    path('invest/', views.invest, name='invest'),
###############################################################################################
    path("create-payment-intent/", views.create_payment_intent, name="create_payment_intent"),
    path("payment-successful/", views.payment_successful, name="payment_successful"),
    path("add-funds/", views.deposit_funds_page, name="deposit_funds"),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('add-funds/success/', views.success_view, name='success'),
    
]   
    
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
