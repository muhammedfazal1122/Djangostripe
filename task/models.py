# task/models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import date, timedelta



class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class APIMetering(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    total_calls = models.BigIntegerField(default=0)
    daily_calls = models.IntegerField(default=0)
    last_reset = models.DateField(null=True)
    
    # Dynamic limits
    daily_limit = models.IntegerField(default=10)
    total_limit = models.BigIntegerField(default=100)

    def reset_daily_calls(self):
        """Reset daily calls counter if a new day has begun."""
        today = date.today()
        if self.last_reset != today:
            self.daily_calls = 0
            self.last_reset = today
            self.save()

    @property
    def is_within_limits(self):
        """Check if API calls are within limits."""
        return (
            self.total_calls < self.total_limit and 
            self.daily_calls < self.daily_limit
        )

    def increment_calls(self):
        """Increment both total and daily call counters."""
        self.reset_daily_calls()  # Ensure daily counter is reset if needed
        
        if not self.is_within_limits:
            raise ValidationError("API call limit exceeded")

        self.total_calls += 1
        self.daily_calls += 1
        self.save()

    def get_remaining_calls(self):
        """Get remaining calls for both limits."""
        self.reset_daily_calls()  # Ensure daily counter is reset if needed
        return {
            'daily': max(0, self.daily_limit - self.daily_calls),
            'total': max(0, self.total_limit - self.total_calls)
        }

    def update_limits(self, daily_limit=None, total_limit=None):
        """Update API call limits."""
        if daily_limit is not None:
            self.daily_limit = daily_limit
        if total_limit is not None:
            self.total_limit = total_limit
        self.save()