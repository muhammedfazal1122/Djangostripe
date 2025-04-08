# serializers.py - Add a serializer for API metrics
from rest_framework import serializers
from .models import Task, APIMetering

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

class APIMetricsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = APIMetering
        fields = ['username', 'get_count', 'post_count', 'put_count', 'delete_count', 
                  'total_count', 'daily_count', 'daily_reset', 'last_request']

