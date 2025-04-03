
from django.urls import path
from .views import task_page, update_task, delete_task,task_list

urlpatterns = [
    path('task/', task_page, name='task_page'),
    path('task/update/<int:task_id>/', update_task, name='update_task'),
    path('task/delete/<int:task_id>/', delete_task, name='delete_task'),

    path('task_list/', task_list, name='task_list'),

]
