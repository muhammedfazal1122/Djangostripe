from datetime import date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Task, APIMetering
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Task, APIMetering

@login_required
def task_page(request):
    tasks = Task.objects.filter(user=request.user)
    metering, _ = APIMetering.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')

        if not title or not description:
            return JsonResponse({'error': 'Title and description are required'}, status=400)

        try:
            metering.increment_calls()
            
            Task.objects.create(
                user=request.user,
                title=title,
                description=description
            )
            
            return redirect('task_page')
            
        except ValidationError as e:
            return JsonResponse(
                {'error': str(e)},
                status=429  # Too Many Requests
            )

    return render(
        request,
        'task_page.html',
        {
            'tasks': tasks,
            'metering': metering,
            'limits': metering.get_remaining_calls(),
        }
    )


@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.save()
        return redirect('task_page')
    
    return render(request, 'task_page.html', {'tasks': Task.objects.filter(user=request.user)})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('task_page')


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    return render(request, 'task_list.html', {'tasks': tasks})



@login_required
def create_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        metering, _ = APIMetering.objects.get_or_create(user=request.user)
        
        # Rate Limiting Logic
        if metering.total_calls >= 100 or metering.daily_calls >= 10:
            return JsonResponse({'error': 'API call limit exceeded'}, status=429)
        
        # Reset Daily Counter if New Day
        if metering.last_reset != date.today():
            metering.daily_calls = 0
            metering.last_reset = date.today()
        
        metering.total_calls += 1
        metering.daily_calls += 1
        metering.save()
        
        Task.objects.create(user=request.user, title=title, description=description)
        return redirect('task_list')

    return render(request, 'create_task.html')