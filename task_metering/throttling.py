from rest_framework.throttling import BaseThrottle
from django.conf import settings
from django.core.cache import cache

from .utils import report_usage_to_stripe
from .models import APIMetering, UserSubscription

class SubscriptionBasedThrottle(BaseThrottle):
    """Custom throttle based on subscription plans"""
    
    def allow_request(self, request, view):
        """
        Check if request should be allowed based on subscription.
        Also tracks API usage for billing.
        """
        # Only apply to authenticated users
        if not request.user or not request.user.is_authenticated:
            return True
            
        print(f"Checking throttle for user {request.user.username}")
        
        try:
            # Get or create API metering for the user
            metering, created = APIMetering.objects.get_or_create(user=request.user)
            
            # For Hard Limit approach: Check if user has exceeded their plan limit
            if getattr(settings, 'USE_HARD_API_LIMITS', True):
                # Check if user has an active subscription with a plan
                try:
                    subscription = UserSubscription.objects.get(user=request.user, is_active=True)
                    if not subscription.plan:
                        # No plan assigned, but active subscription - might be a free tier
                        # You can customize this logic based on your business rules
                        plan_limit = 0  # Default to no access or customize as needed
                    else:
                        plan_limit = subscription.plan.base_api_calls
                        
                    # If limit exceeded, deny the request
                    if metering.daily_count >= plan_limit:
                        print(f"Request DENIED - User has exceeded their limit. Daily count: {metering.daily_count}, Limit: {plan_limit}")
                        return False
                    
                except UserSubscription.DoesNotExist:
                    # No active subscription
                    free_tier_limit = getattr(settings, 'FREE_TIER_API_LIMIT', 0)
                    if metering.daily_count >= free_tier_limit:
                        print(f"Request DENIED - User has no subscription. Daily count: {metering.daily_count}, Free limit: {free_tier_limit}")
                        return False
            
            # Now track the usage (only if we're allowing the request)
            metering.increment(request.method)
            
            # Report metered usage to Stripe if needed
            if getattr(settings, 'USE_STRIPE_METERED_BILLING', False):
                try:
                    subscription = UserSubscription.objects.get(user=request.user, is_active=True)
                    if subscription.plan:
                        # Report usage to Stripe
                        report_usage_to_stripe(request.user, 1)  # Report 1 API call
                except UserSubscription.DoesNotExist:
                    pass
                    

            print(f"Request ALLOWED - User {request.user.username} daily count: {metering.daily_count}")
            return True
            
        except Exception as e:
            print(f"Throttling error: {str(e)}")
            return True  # Default to allowing in case of errors
    
    def wait(self):
        """
        Returns the recommended next request time in seconds.
        """
        return 24 * 60 * 60  # Suggest waiting 24 hours

# Removed UserDailyRateThrottle that depends on views.report_usage_to_stripe