from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from .models import Task, APIMetering
from .serializers import TaskSerializer, APIMeteringSerializer

class TaskListCreateView(APIView):
    """API: Get list of tasks & Create a task."""
    permission_classes = [IsAuthenticated]

    @ratelimit(key='user', rate='100/d', method=['GET'], block=True)
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @ratelimit(key='user', rate='50/d', method=['POST'], block=True)
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskDetailView(APIView):
    """API: Retrieve, Update or Delete a specific task."""
    permission_classes = [IsAuthenticated]

    def get_object(self, task_id, user):
        return get_object_or_404(Task, id=task_id, user=user)

    @ratelimit(key='user', rate='100/d', method=['GET'], block=True)
    def get(self, request, task_id):
        task = self.get_object(task_id, request.user)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    @ratelimit(key='user', rate='50/d', method=['PUT'], block=True)
    def put(self, request, task_id):
        task = self.get_object(task_id, request.user)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @ratelimit(key='user', rate='20/d', method=['DELETE'], block=True)
    def delete(self, request, task_id):
        task = self.get_object(task_id, request.user)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class APIMeteringView(APIView):
    """API: Retrieve API usage stats."""
    permission_classes = [IsAuthenticated]

    @ratelimit(key='user', rate='50/d', method=['GET'], block=True)
    def get(self, request):
        metering, _ = APIMetering.objects.get_or_create(user=request.user)
        serializer = APIMeteringSerializer(metering)
        return Response(serializer.data)