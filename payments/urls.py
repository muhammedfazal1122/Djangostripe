
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Subscription Plans
    # JWT Authentication Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', views.RegisterView.as_view(), name='register'),
    # path('api/login/', views.LoginView.as_view(), name='login'),
    # path('api/logout/', views.LogoutView.as_view(), name='logout'),
    
    path('logout/', views.logout_view, name='logout'),

    path('', views.home, name='home'),
    path('plans/', views.list_subscription_plans, name='subscription_plans'),
    path('subscribe_to_plan/<int:plan_id>/', views.subscribe_to_plan, name='subscribe_to_plan'),

    path("get_subscribe/<int:subscription_id>/", views.get_subscription, name="get_subscription"),
    path("update_subscription/<int:subscription_id>/update/", views.update_subscription, name="update_subscription"),
    path("cancel_subscription/<int:subscription_id>/cancel/", views.cancel_subscription, name="cancel_subscription"),


    path('add-payment-method/', views.add_payment_method, name='add_payment_method'),
    # path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('tasks/', views.billing_dashboard, name='billing_dashboard'),
    # path('billing/success/', views.billingsuccess, name='success'),
    


]
