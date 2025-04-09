from django.urls import path
from .views import (
    TaskListCreateView, 
    TaskDetailView, 
    APIMetricsView,
    SubscriptionPlansView,
    CreateCheckoutSessionView,
    SubscriptionWebhookView,
    UserSubscriptionStatusView,
    Successpage
)

urlpatterns = [
    # Existing URLs
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('metrics/', APIMetricsView.as_view(), name='api-metrics'),
    
    # Subscription URLs
    path('subscription/plans/', SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('subscription/checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('subscription/webhook/', SubscriptionWebhookView.as_view(), name='subscription-webhook'),
    path('subscription/status/', UserSubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/success/', Successpage.as_view(), name='Successpage'),
]