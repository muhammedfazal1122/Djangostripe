# views.py - Example API view implementation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .throttling import UserRateThrottle
from .models import Task, APIMetering
from .serializers import TaskSerializer, APIMetricsSerializer
from datetime import date  # ✅ REQUIRED



class TaskListCreateView(APIView):
    """API: Get list of tasks & Create a task."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskDetailView(APIView):
    """API: Retrieve, Update or Delete a specific task."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_object(self, task_id, user):
        return get_object_or_404(Task, id=task_id, user=user)
    
    def get(self, request, task_id):
        task = self.get_object(task_id, request.user)
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def put(self, request, task_id):
        task = self.get_object(task_id, request.user)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, task_id):
        task = self.get_object(task_id, request.user)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class APIMetricsView(APIView):
    """API: View your API usage metrics."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        metering, created = APIMetering.objects.get_or_create(user=request.user)
        
        # Display the current counter values
        data = {
            'username': request.user.username,
            'total_requests': metering.total_count,
            'daily_requests': metering.daily_count,
            'get_requests': metering.get_count,
            'post_requests': metering.post_count,
            'put_requests': metering.put_count,
            'delete_requests': metering.delete_count,
            'last_request': metering.last_request,
        }
        
        return Response(data)
