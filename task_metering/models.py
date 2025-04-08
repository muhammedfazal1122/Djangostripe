# models.py - Add or update your APIMetering model
from django.contrib.auth.models import User
from django.db import models
from datetime import date  # ✅ REQUIRED

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks_metering')
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class APIMetering(models.Model):
    """Track API usage per user with method-specific counters"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='api_usage')
    get_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    put_count = models.IntegerField(default=0)
    delete_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    daily_count = models.IntegerField(default=0)
    daily_reset = models.DateField(auto_now=True)
    last_request = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"API usage for {self.user.username}"
    
    def increment(self, method):
        """Increment the appropriate counter based on HTTP method"""
        # Update total count
        self.total_count += 1
        
        # Reset daily count if it's a new day
        today = date.today()
        if self.daily_reset != today:
            self.daily_count = 0
            self.daily_reset = today
        
        # Update daily count
        self.daily_count += 1
        
        # Update method-specific counter
        method = method.upper()
        if method == 'GET':
            self.get_count += 1
        elif method == 'POST':
            self.post_count += 1
        elif method == 'PUT' or method == 'PATCH':
            self.put_count += 1
        elif method == 'DELETE':
            self.delete_count += 1
        
        self.save()
