# throttling.py
from rest_framework.throttling import BaseThrottle
from django.conf import settings
from django.core.cache import cache
import stripe

from .models import APIMetering, UserSubscription


class SubscriptionBasedThrottle(BaseThrottle):
    """Custom throttle based on subscription plans"""

    def allow_request(self, request, view):
        """
        Check if request should be allowed based on subscription.
        Usage tracking is now handled by middleware and signals.
        """
        # Only apply to authenticated users
        if not request.user or not request.user.is_authenticated:
            return True

        # For Hard Limit approach: Check if user has exceeded their plan limit
        if getattr(settings, 'USE_HARD_API_LIMITS', True):
            try:
                # Get API metering for the user
                metering = APIMetering.objects.get(user=request.user)
                
                # Check if user has an active subscription with a plan
                try:
                    subscription = UserSubscription.objects.get(user=request.user, is_active=True)
                    if not subscription.plan:
                        # No plan assigned, but active subscription - might be a free tier
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
                        
            except APIMetering.DoesNotExist:
                # No metering record yet, they haven't made any API calls
                pass
        
        # Request is allowed
        return True

    def wait(self):
        """
        Returns the recommended next request time in seconds.
        """
        return 24 * 60 * 60  # Suggest waiting 24 hours