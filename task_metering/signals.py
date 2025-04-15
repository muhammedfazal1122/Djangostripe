from django.dispatch import Signal, receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import date
import logging
import stripe

from .models import UserSubscription

# Create a custom signal for API calls
api_call_made = Signal()

# Setup logging
logger = logging.getLogger(__name__)

@receiver(api_call_made)
def process_api_call(sender, **kwargs):
    """
    Process the API call signal by updating usage metrics and reporting to Stripe.
    Pure usage-based tracking without any throttling or hard limits.
    """
    from .models import APIMetering, UserSubscription, APIUsageBilling
    
    user = kwargs.get('user')
    method = kwargs.get('method', '')
    path = kwargs.get('path', '')
    status_code = kwargs.get('status_code', 0)
    timestamp = kwargs.get('timestamp', timezone.now())

    if not user or not user.is_authenticated:
        return

    try:
        print(f"[{timezone.now()}][SIGNAL] API usage signal received for {user.username}: {method} {path} ({status_code})")
        # Get or create API metering record for the user
        metering, created = APIMetering.objects.get_or_create(user=user)
        today = date.today()
        
        # Reset daily count if it's a new day
        if metering.last_reset_date != today:
            metering.daily_count = 0
            metering.last_reset_date = today
        
        # Update usage counts
        metering.total_count += 1
        metering.daily_count += 1
        metering.billing_cycle_count += 1
        metering.last_request = timestamp
        
        # Track usage by HTTP method
        if method == 'GET':
            metering.get_count += 1
        elif method == 'POST':
            metering.post_count += 1
        elif method == 'PUT' or method == 'PATCH':
            metering.put_count += 1
        elif method == 'DELETE':
            metering.delete_count += 1
            
        metering.save()
        logger.debug(f"API usage recorded for user {user.username}: {method} {path}")
        print(f"API usage recorded for user {user.username}: {method} {path}")
        
        # Update usage billing record for today
        usage, created = APIUsageBilling.objects.get_or_create(
            user=user, 
            date=today
        )
        usage.call_count += 1
        usage.save()
        
        # Calculate overage for billing
        usage.calculate_overage()
        print(f"Usage billing updated for user {user.username}: {usage.call_count} calls today")
        
        # Report usage to Stripe
        try:
            print(f"Checking subscription for user {user.username}, is_active: {user.is_active}")  
            
            subscription = UserSubscription.objects.get(user=user, is_active=True)
            print(f"Found active subscription for {user.username}: customer_id={subscription.stripe_customer_id}, subscription_id={subscription.stripe_subscription_id}")
            
            # Only report to Stripe if the user has valid Stripe IDs
            if subscription.stripe_customer_id:
                print(f"Initiating Stripe usage report for {user.username}")    
                report_usage_to_stripe(user)
        except UserSubscription.DoesNotExist:
            print(f"No active subscription found for user {user.username}")
            pass

                
    except Exception as e:
        logger.error(f"Error processing API call signal: {str(e)}")
        print(f"[ERROR] Processing API call signal: {str(e)}")

def report_usage_to_stripe(user, count=1):
    """
    Report API usage to Stripe's Meter API
    """
    from .models import UserSubscription
    
    try:
        print(f"Starting Stripe usage reporting for user {user.username}")
        # Get user's subscription for their Stripe customer ID
        subscription = UserSubscription.objects.get(user=user, is_active=True)
        print(f"Confirmed active subscription: customer_id={subscription.stripe_customer_id}, subscription_id={subscription.stripe_subscription_id}")
        
        if not subscription.stripe_customer_id:
            print(f"No Stripe customer ID for user {user.username}")
            logger.warning(f"No Stripe customer ID for user {user.username}")
            return False

        if not settings.STRIPE_TEST_SECRET_KEY:
            print(f"Stripe API key not configured")
            logger.warning("Stripe API key not configured")
            return False

        # Set Stripe API key
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        print(f"Using Stripe API key: {stripe.api_key[:5]}...{stripe.api_key[-4:] if len(stripe.api_key) > 8 else ''}")
        
        # According to Stripe documentation for Meter Event:
        # https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api
        
        print(f"Creating Stripe Billing MeterEvent with: event_name='api_calls', payload={{value: {count}, stripe_customer_id: {subscription.stripe_customer_id}}}")
        
        # FIXED CODE: Use correct parameter structure according to Stripe documentation
        result = stripe.billing.MeterEvent.create(
            event_name="api_signals",  # The meter name configured in Stripe
            payload={
                "value": str(count),  # Value must be sent as string according to docs
                "stripe_customer_id": subscription.stripe_customer_id
            }
        )
        
        print(f"Stripe Meter Event created successfully: {result}")
        
        logger.info(f"Reported {count} API calls for user {user.username} to Stripe Meter")
        return True
    except UserSubscription.DoesNotExist:
        print(f"No active subscription found for user {user.username}")
        logger.warning(f"No active subscription found for user {user.username}")
        return False
    except Exception as e:
        print(f"[ERROR] Stripe usage reporting failed: {str(e)}")
        logger.error(f"Error reporting usage to Stripe: {str(e)}")
        return False

# Add signal to reset billing cycle counts at end of billing period
@receiver(post_save, sender=UserSubscription)
def handle_subscription_renewal(sender, instance, **kwargs):
    """
    If a subscription period has been renewed, reset the billing cycle count
    """
    if kwargs.get('created', False):
        return  # Skip for newly created subscriptions
        
    if instance.is_active and instance.current_period_start and instance.current_period_end:
        # This is a subscription renewal
        from .models import APIMetering
        
        try:
            metering = APIMetering.objects.get(user=instance.user)
            # Reset the billing cycle counter
            metering.billing_cycle_count = 0
            metering.save()
            logger.info(f"Reset billing cycle counter for user {instance.user.username}")
            print(f"Reset billing cycle counter for user {instance.user.username}")
        except APIMetering.DoesNotExist:
            print(f"No API metering record found for user {instance.user.username}")
            pass