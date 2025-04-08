# models.py - Add subscription and usage models
from django.db import models
from django.contrib.auth.models import User
from datetime import date
import stripe
from django.conf import settings

# Configure Stripe API key
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

class SubscriptionPlan(models.Model):
    """Defines the available subscription plans"""
    PLAN_TYPES = (
        ('beginner', 'Beginner'),
        ('pro', 'Pro'),
    )
    
    name = models.CharField(max_length=50, choices=PLAN_TYPES)
    stripe_price_id = models.CharField(max_length=100)
    base_api_calls = models.IntegerField(default=10)  # Free API calls included
    overage_unit_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.50)  # Price per additional call
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} Plan"

class UserSubscription(models.Model):
    """Tracks a user's subscription status"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='metering_subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s {self.plan.name if self.plan else 'No'} Subscription"
    
    def get_api_call_limit(self):
        """Get the maximum API calls allowed for this subscription"""
        if not self.is_active or not self.plan:
            return 0
        return self.plan.base_api_calls

class APIUsageBilling(models.Model):
    """Tracks API usage for billing purposes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metering_api_billing')
    date = models.DateField(default=date.today)
    call_count = models.IntegerField(default=0)
    overage_count = models.IntegerField(default=0)  # Calls exceeding the base limit
    billed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_billed = models.BooleanField(default=False)
    stripe_invoice_item_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        unique_together = ('user', 'date')
    
    def __str__(self):
        return f"{self.user.username}'s usage on {self.date}"
    
    def calculate_overage(self):
        """Calculate overage based on subscription plan"""
        try:
            subscription = UserSubscription.objects.get(user=self.user, is_active=True)
            if subscription.plan:
                base_limit = subscription.plan.base_api_calls
                if self.call_count > base_limit:
                    self.overage_count = self.call_count - base_limit
                    # Calculate billed amount based on subscription tier
                    self.billed_amount = self.overage_count * float(subscription.plan.overage_unit_amount)
                else:
                    self.overage_count = 0
                    self.billed_amount = 0
            self.save()
        except UserSubscription.DoesNotExist:
            self.overage_count = self.call_count  # All calls are overage if no subscription
            self.billed_amount = 0  # Don't bill users without a plan
            self.save()
    
    def create_stripe_invoice_item(self):
        """Create a Stripe invoice item for overage charges"""
        if self.overage_count > 0 and self.billed_amount > 0 and not self.is_billed:
            try:
                subscription = UserSubscription.objects.get(user=self.user, is_active=True)
                if subscription.stripe_customer_id:
                    # Create invoice item in Stripe
                    invoice_item = stripe.InvoiceItem.create(
                        customer=subscription.stripe_customer_id,
                        amount=int(self.billed_amount * 100),  # Convert to cents
                        currency='usd',
                        description=f"API Usage Overage ({self.overage_count} calls) on {self.date}",
                        metadata={
                            'user_id': self.user.id,
                            'date': str(self.date),
                            'call_count': self.call_count,
                            'overage_count': self.overage_count
                        }
                    )
                    self.stripe_invoice_item_id = invoice_item.id
                    self.is_billed = True
                    self.save()
                    return True
            except UserSubscription.DoesNotExist:
                pass
        return False

# Enhanced APIMetering model that works with subscriptions
class APIMetering(models.Model):
    """Track API usage for throttling and billing"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='api_usage')
    get_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    put_count = models.IntegerField(default=0)
    delete_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    daily_count = models.IntegerField(default=0)
    billing_cycle_count = models.IntegerField(default=0)  # Resets on billing cycle
    last_reset_date = models.DateField(default=date.today)
    last_request = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"API usage for {self.user.username}"
    
    def increment(self, method):
        """Increment the appropriate counter and handle usage tracking for billing"""
        today = date.today()
        
        # Reset daily count if it's a new day
        if self.last_reset_date != today:
            self.daily_count = 0
            self.last_reset_date = today
        
        # Increment all the counters
        self.total_count += 1
        self.daily_count += 1
        self.billing_cycle_count += 1
        
        # Update method-specific counter
        method = method.upper()
        if method == 'GET':
            self.get_count += 1
        elif method == 'POST':
            self.post_count += 1
        elif method == 'PUT' or method == 'PATCH':
            self.put_count += 1
        elif method == 'DELETE':
            self.delete_count += 1
        
        # Track usage for billing
        usage, created = APIUsageBilling.objects.get_or_create(
            user=self.user, 
            date=today
        )
        usage.call_count += 1
        usage.save()
        
        # Calculate overage for real-time usage tracking
        usage.calculate_overage()
        
        self.save()
    
    def is_limit_exceeded(self):
        """Check if user has exceeded their subscription limit (for hard limits)"""
        try:
            subscription = UserSubscription.objects.get(user=self.user, is_active=True)
            # For hard limit approach - check if daily count exceeds plan limit
            if subscription.plan:
                return self.daily_count >= subscription.plan.base_api_calls
            return True  # No plan means no access
        except UserSubscription.DoesNotExist:
            return True  # No subscription means no access



class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks_metering')
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
