from rest_framework import serializers
from .models import Task, APIMetering

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'created_at']

class APIMeteringSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIMetering
        fields = ['total_calls', 'daily_calls', 'daily_limit', 'total_limit']
