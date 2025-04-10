
from .tasks import report_usage_to_stripe_task
def report_usage_to_stripe(user, count):
    """
    Report API usage to Stripe for metered billing
    
    Args:
        user: The user whose usage is being reported
        count: The number of API calls to report
    """
    
    # Offload to Celery
    report_usage_to_stripe_task.delay(user.id, count)