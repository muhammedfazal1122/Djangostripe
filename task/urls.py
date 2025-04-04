from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import TaskListCreateView, TaskDetailView, APIMeteringView

urlpatterns = [
    # DRF API Endpoints (JWT Protected)
    path('api/tasks/', TaskListCreateView.as_view(), name='api_task_list_create'),
    path('api/tasks/<int:task_id>/', TaskDetailView.as_view(), name='api_task_detail'),
    path('api/metering/', APIMeteringView.as_view(), name='api_metering'),


]
