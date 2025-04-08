# throttling.py - Create a custom throttle class
from rest_framework.throttling import SimpleRateThrottle
from django.utils import timezone
from datetime import date
from .models import APIMetering

class UserRateThrottle(SimpleRateThrottle):
    """
    Throttles requests by user and tracks API usage metrics.
    """
    scope = 'user'
    
    def get_cache_key(self, request, view):
        """
        Generate a cache key only for authenticated users.
        """
        print(f"THROTTLE: get_cache_key called for user {request.user}")

        if not request.user or not request.user.is_authenticated:
            return None  # Don't throttle unauthenticated requests
        
        return f"throttle_{self.scope}_{request.user.pk}"
    
    def allow_request(self, request, view):
        print(f"THROTTLE: allow_request called for {request.method} to {request.path}")

        """
        Check if request should be allowed and track API usage.
        """
        # Track API usage for authenticated users regardless of throttling
        if request.user and request.user.is_authenticated:
            self._track_api_usage(request)
            
        # Let the parent class handle the actual throttling
        return super().allow_request(request, view)
        
    def _track_api_usage(self, request):
        """
        Track API usage metrics in the database.
        """
        print(f"THROTTLE: _track_api_usage called for {request.user.username}")
        metering, created = APIMetering.objects.get_or_create(user=request.user)
        print(f"BEFORE: total_count={metering.total_count}, get_count={metering.get_count}")
        old_count = metering.total_count  # Save old count for comparison
        metering.increment(request.method)
        
        # Print debugging information
        print(f"API Call: User {request.user.username} - {request.method} request to {request.path}")
        print(f"Counter increased from {old_count} to {metering.total_count}")
        print(f"Method counts: GET={metering.get_count}, POST={metering.post_count}, PUT={metering.put_count}, DELETE={metering.delete_count}")