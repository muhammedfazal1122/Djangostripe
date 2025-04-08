from django.contrib import admin
from .models import Task, APIMetering

@admin.register(APIMetering)
class APIMetricsAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_count', 'post_count', 'put_count', 'delete_count', 'total_count', 'daily_count']
    readonly_fields = ['get_count', 'post_count', 'put_count', 'delete_count', 'total_count', 'daily_count', 'daily_reset', 'last_request']

admin.site.register(Task)