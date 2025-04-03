from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
from .views import (
    task_page, update_task, delete_task, 
    TaskListCreateView, TaskDetailView, APIMeteringView
)

urlpatterns = [
    # Django Template Views
    path('tasks/', task_page, name='task_page'),
    path('tasks/update/<int:task_id>/', update_task, name='update_task'),
    path('tasks/delete/<int:task_id>/', delete_task, name='delete_task'),

    # DRF API Endpoints (JWT Protected)
    path('api/tasks/', TaskListCreateView.as_view(), name='api_task_list_create'),
    path('api/tasks/<int:task_id>/', TaskDetailView.as_view(), name='api_task_detail'),
    path('api/metering/', APIMeteringView.as_view(), name='api_metering'),

    # JWT Authentication Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login to get access & refresh tokens
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh expired access token
]
