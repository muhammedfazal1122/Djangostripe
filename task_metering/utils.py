# utils.py - Stripe metering utilities
import stripe
from django.conf import settings
from django.utils import timezone
from celery import shared_task

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

def get_subscription_item_id(stripe_subscription_id):
    """
    Get the subscription item ID for a given subscription.
    For metered billing, we need the subscription item ID, not the subscription ID.
    """
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        # For simplicity, we're assuming one subscription item per subscription
        # In a more complex system, you might need to identify which item to meter
        if subscription.items.data:
            return subscription.items.data[0].id
        return None
    except stripe.error.StripeError as e:
        print(f"Error retrieving subscription items: {str(e)}")
        return None

def report_usage_to_stripe(user, count=1):
    """
    Report API usage to Stripe for metered billing.
    This function just queues the task to avoid blocking the request.
    """
    from .tasks import report_usage_to_stripe_task
    
    # Queue the task to report usage asynchronously
    report_usage_to_stripe_task.delay(user.id, count)
    return True

def update_subscription_details(subscription_model):
    """
    Update local subscription details from Stripe
    """
    if not subscription_model.stripe_subscription_id:
        return False
        
    try:
        stripe_sub = stripe.Subscription.retrieve(subscription_model.stripe_subscription_id)
        
        # Update local subscription data
        subscription_model.current_period_start = timezone.datetime.fromtimestamp(
            stripe_sub.current_period_start, tz=timezone.get_current_timezone())
        subscription_model.current_period_end = timezone.datetime.fromtimestamp(
            stripe_sub.current_period_end, tz=timezone.get_current_timezone())
        subscription_model.is_active = stripe_sub.status == 'active'
        subscription_model.save()
        
        return True
    except stripe.error.StripeError as e:
        print(f"Error updating subscription {subscription_model.id}: {str(e)}")
        return False