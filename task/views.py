from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Task, APIMetering
from .serializers import TaskSerializer, APIMeteringSerializer

class TaskListCreateView(APIView):
    """Handles listing and creating tasks."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all tasks for the authenticated user."""
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new task while enforcing API metering."""
        metering, _ = APIMetering.objects.get_or_create(user=request.user)

        try:
            metering.increment_calls()  # Check & increment API calls
        except Exception as e:
            return Response({"error": str(e)}, status=429)

        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)

class TaskDetailView(APIView):
    """Handles updating and deleting a task."""
    permission_classes = [IsAuthenticated]

    def get_object(self, task_id, user):
        """Retrieve the task or return 404 if not found."""
        return get_object_or_404(Task, id=task_id, user=user)

    def put(self, request, task_id):
        """Update a task."""
        task = self.get_object(task_id, request.user)
        serializer = TaskSerializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=400)

    def delete(self, request, task_id):
        """Delete a task."""
        task = self.get_object(task_id, request.user)
        task.delete()
        return Response(status=204)

class APIMeteringView(APIView):
    """Returns API metering info for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        metering, _ = APIMetering.objects.get_or_create(user=request.user)
        serializer = APIMeteringSerializer(metering)
        return Response(serializer.data)
