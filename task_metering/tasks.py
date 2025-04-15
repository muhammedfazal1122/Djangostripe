from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
import logging
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def reset_daily_counters():
    """
    Reset daily API usage counters - typically scheduled to run at midnight
    """
    from .models import APIMetering
    
    today = date.today()
    
    # Find all metering records where last reset date is not today
    records = APIMetering.objects.exclude(last_reset_date=today)
    count = 0
    
    # Reset the daily counters and update last_reset_date
    for record in records:
        record.daily_count = 0
        record.last_reset_date = today
        record.save()
        count += 1
        
    logger.info(f"Reset daily API usage counters for {count} users")
    return count

@shared_task
def process_usage_billing():
    """
    Process usage billing records and create Stripe invoice items
    This can run daily or weekly depending on your billing cycle
    """
    from .models import APIUsageBilling
    
    yesterday = date.today() - timedelta(days=1)
    
    # Find all unbilled usage records from yesterday with overage
    billing_records = APIUsageBilling.objects.filter(
        date=yesterday,
        is_billed=False,
        overage_count__gt=0
    )
    
    for record in billing_records:
        success = record.create_stripe_invoice_item()
        if success:
            logger.info(f"Created Stripe invoice item for user {record.user.username}")
    
    return len(billing_records)

# @shared_task
# def sync_stripe_metered_usage():
#     """
#     Backup task to ensure Stripe metered usage is in sync
#     This can be run once a day to catch any missed real-time reports
#     """
#     from .models import APIMetering, UserSubscription
    
#     # Get all active subscriptions
#     subscriptions = UserSubscription.objects.filter(
#         is_active=True,
#         stripe_customer_id__isnull=False,
#         stripe_subscription_id__isnull=False
#     )
    
#     count = 0
#     for subscription in subscriptions:
#         try:
#             # Get the metering record
#             metering = APIMetering.objects.get(user=subscription.user)
            
#             # Report daily count to Stripe
#             stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
            
#             # Get yesterday's billing record
#             yesterday = date.today() - timedelta(days=1)
#             from .models import APIUsageBilling
            
#             try:
#                 usage = APIUsageBilling.objects.get(
#                     user=subscription.user, 
#                     date=yesterday
#                 )
                
#                 # Report yesterday's usage to Stripe
#                 if usage.call_count > 0:
#                     result = stripe.billing.MeterEvent.create(
#                         event_name="api_calls",
#                         customer=subscription.stripe_customer_id,
#                         value=usage.call_count
#                     )
#                     count += 1
#                     logger.info(f"Synced {usage.call_count} API calls for user {subscription.user.username} to Stripe")
                    
#             except APIUsageBilling.DoesNotExist:
#                 pass
                
#         except APIMetering.DoesNotExist:
#             pass
    
#     return count