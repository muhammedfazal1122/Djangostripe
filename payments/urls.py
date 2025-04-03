
from django.urls import path
from . import views

urlpatterns = [
    # Subscription Plans
    
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
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
