from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Task, APIMetering
from .serializers import TaskSerializer, APIMeteringSerializer
from django.http import JsonResponse

@login_required
def task_page(request):
    """Renders the Task Manager template with tasks & API metering details."""
    tasks = Task.objects.filter(user=request.user)
    metering, _ = APIMetering.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        # Create a new task
        title = request.POST.get("title")
        description = request.POST.get("description")

        try:
            metering.increment_calls()  # Check & increment API calls
            Task.objects.create(user=request.user, title=title, description=description)
        except Exception as e:
            return render(request, "tasks/task_list.html", {
                "tasks": tasks,
                "metering": metering,
                "error": str(e),
            })
        
        return redirect("task_page")  # Redirect to avoid resubmission
    
    return render(request, "task_page.html", {
        "tasks": tasks,
        "metering": metering,
        "total_limit": metering.total_limit,
        "daily_limit": metering.daily_limit,
    })

@login_required
def update_task(request, task_id):
    """Handles updating a task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == "POST":
        task.title = request.POST.get("title")
        task.description = request.POST.get("description")
        task.save()
    
    return redirect("task_page")

@login_required
def delete_task(request, task_id):
    """Handles deleting a task."""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect("task_page")

# === DRF API Views with JWT Authentication ===

class TaskListCreateView(APIView):
    """API: Get list of tasks & Create a task."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all tasks for authenticated user."""
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a task with API metering."""
        metering, _ = APIMetering.objects.get_or_create(user=request.user)

        try:
            metering.increment_calls()  # Enforce API limit
        except Exception as e:
            return Response({"error": str(e)}, status=429)

        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)

class TaskDetailView(APIView):
    """API: Update/Delete a specific task."""
    permission_classes = [IsAuthenticated]

    def get_object(self, task_id, user):
        """Retrieve task or return 404 if not found."""
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
    """API: Retrieve API usage stats."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        metering, _ = APIMetering.objects.get_or_create(user=request.user)
        serializer = APIMeteringSerializer(metering)
        return Response(serializer.data)
