from django.urls import path
from .views import (
    TaskListCreateView, 
    TaskDetailView,
    APIMetricsView,
    SubscriptionPlansView,
    CancelSubscriptionView,
    UpdateSubscriptionView,
    CreateCheckoutSessionView,
    SubscriptionWebhookView,
    UserSubscriptionStatusView,
    Successpage,
    AdminAPIUsageView,
    UserAPIUsageView,
)

urlpatterns = [
    # Task API URLs
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),  # Fixed missing task_id parameter
    path('metrics/', APIMetricsView.as_view(), name='api-metrics'),
    
    # Subscription URLs
    path('subscription/plans/', SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('subscription/checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscription/update/', UpdateSubscriptionView.as_view(), name='update-subscription'),
    path('subscription/status/', UserSubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/success/', Successpage.as_view(), name='Successpage'),
    
    # API Usage
    path('api/admin/usage/', AdminAPIUsageView.as_view(), name='admin-api-usage'),
    path('api/usage/', UserAPIUsageView.as_view(), name='user-api-usage'),
    
    # Webhook endpoint (for Stripe CLI and live webhooks)
    path('webhook', SubscriptionWebhookView.as_view(), name='subscription-webhook-direct'),
]