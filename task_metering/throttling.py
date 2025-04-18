from rest_framework.throttling import BaseThrottle
from .models import UserSubscription, APIMetering

class SubscriptionBasedThrottle(BaseThrottle):
    """
    Throttle based on user's subscription status.
    - Users with active subscriptions get limits based on their plan
    - Users without subscriptions are limited to 5 API calls total
    """
    FREE_USER_LIMIT = 5  # Maximum API calls for users without subscriptions
    
    def allow_request(self, request, view):
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
            
        # Get or create API usage metrics for this user
        metering, created = APIMetering.objects.get_or_create(user=user)
        
        # Check if user has an active subscription
        try:
            subscription = UserSubscription.objects.get(user=user, is_active=True)
            # If subscription exists and is active, allow the request
            # (actual consumption gets tracked by the middleware)
            return True
        except UserSubscription.DoesNotExist:
            # For users without subscriptions, check if they've exceeded free limit
            if metering.total_count >= self.FREE_USER_LIMIT:
                return False
            return True
    
    def wait(self):
        # No wait time - once the limit is reached, it's reached
        return None