# tasks.py
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
import stripe
from django.conf import settings
from datetime import date, timedelta

from .models import UserSubscription, APIUsageBilling, APIMetering

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

@shared_task
def process_daily_api_usage():
    """
    Task to process API usage billing at the end of each day
    """
    yesterday = date.today() - timedelta(days=1)
    print(f"_____________Processing API usage for {yesterday}")
    
    # Get all usage records for yesterday
    usages = APIUsageBilling.objects.filter(
        date=yesterday,
        is_billed=False,
        overage_count__gt=0,
        billed_amount__gt=0
    )
    
    for usage in usages:
        # Create Stripe invoice item
        if usage.create_stripe_invoice_item():
            print(f"_______________Created invoice item for user {usage.user.username} - ${usage.billed_amount}")
    
    return f"____________Processed {usages.count()} usage records for {yesterday}"




@shared_task
def reset_daily_counters():
    """
    Task to reset daily API counters
    """
    # Get all API metering records
    meterings = APIMetering.objects.all()
    count = 0
    
    for metering in meterings:
        if metering.last_reset_date != date.today():
            metering.daily_count = 0
            metering.last_reset_date = date.today()
            metering.save()
            count += 1
    
    return f"Reset {count} daily counters"

@shared_task
def check_billing_cycles():
    """
    Task to check for subscription billing cycles and reset counters
    """
    now = timezone.now()
    
    # Get all active subscriptions
    subscriptions = UserSubscription.objects.filter(is_active=True)
    count = 0
    
    for subscription in subscriptions:
        # Check if we're at the start of a new billing cycle
        if subscription.current_period_end and subscription.current_period_end <= now:
            # Get updated subscription data from Stripe
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                
                # Update subscription period
                subscription.current_period_start = stripe_sub.current_period_start
                subscription.current_period_end = stripe_sub.current_period_end
                subscription.is_active = stripe_sub.status == 'active'
                subscription.save()
                
                # Reset billing cycle counters
                if subscription.is_active:
                    metering, created = APIMetering.objects.get_or_create(user=subscription.user)
                    metering.billing_cycle_count = 0
                    metering.save()
                    count += 1
                    
            except stripe.error.StripeError as e:
                print(f"Error updating subscription {subscription.id}: {str(e)}")
    
    return f"Checked {subscriptions.count()} subscriptions, reset {count} billing cycles"






@shared_task
def report_usage_to_stripe_task(user_id, count):
    """
    Task to report a single user's API usage to Stripe
    """
    try:
        subscription = UserSubscription.objects.get(user_id=user_id)
        if not subscription.stripe_subscription_id:
            return f"No Stripe subscription for user {user_id}"

        stripe.SubscriptionItem.create_usage_record(
            subscription.stripe_subscription_id,
            quantity=count,
            timestamp=int(timezone.now().timestamp()),
            action='increment',
        )
        message = f"✅ Reported {count} API calls for user {user_id} to Stripe"
        print(message)
        return message
    except Exception as e:
        error_message = f"❌ Error reporting usage for user {user_id}: {str(e)}"
        print(error_message)
        return error_message


@shared_task
def report_all_users_usage():
    """
    Task to report overage usage for all users to Stripe
    """
    today = timezone.now().date()
    reported = 0

    for metering in APIMetering.objects.all():
        try:
            usage = APIUsageBilling.objects.get(user=metering.user, date=today)
            count = usage.overage_count
            if count > 0:
                report_usage_to_stripe_task.delay(metering.user.id, count)
                reported += 1
        except APIUsageBilling.DoesNotExist:
            continue

    return f"Queued Stripe usage reports for {reported} users"