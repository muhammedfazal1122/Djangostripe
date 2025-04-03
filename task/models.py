# task/models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from django.core.exceptions import ValidationError



class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)





class APIMetering(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_calls = models.IntegerField(default=0)
    daily_calls = models.IntegerField(default=0)
    last_reset = models.DateField(default=date.today)  # ✅ Set default value

    # Dynamic limits
    daily_limit = models.IntegerField(default=10)
    total_limit = models.IntegerField(default=100)

    def reset_daily_calls(self):
        """ Reset daily calls if a new day has started. """
        if self.last_reset != date.today():
            self.daily_calls = 0
            self.last_reset = date.today()
            self.save()

    def increment_calls(self):
        """ Increment API call count, enforcing limits. """
        self.reset_daily_calls()

        if self.total_calls >= self.total_limit:
            raise ValidationError("Total API call limit exceeded.")
        if self.daily_calls >= self.daily_limit:
            raise ValidationError("Daily API call limit exceeded.")

        self.total_calls += 1
        self.daily_calls += 1
        self.save()

    def get_remaining_calls(self):
        """ Return remaining API calls for user. """
        return {
            "daily_remaining": max(0, self.daily_limit - self.daily_calls),
            "total_remaining": max(0, self.total_limit - self.total_calls),
        }

    def __str__(self):
        return f"{self.user.username} - {self.daily_calls}/{self.daily_limit} today"
