# payments/models.py
from django.db import models
from django.contrib.auth.models import User

class SubscriptionPlan(models.Model):
    """
    Defines different subscription tiers
    """
    TIER_CHOICES = [
        ('FREE', 'Free'),
        ('STARTER', 'Starter'),
        ('PROFESSIONAL', 'Professional'),
    ]

    name = models.CharField(max_length=100, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stripe_price_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    api_calls_per_month = models.PositiveIntegerField(default=1000)  # Limit per tier
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ${self.price}/month"


class StripeCustomer(models.Model):
    """
    Stores Stripe customer information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    is_active_customer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stripe Customer for {self.user.username}"


class Subscription(models.Model):
    """
    Tracks user subscriptions
    """
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
    ]

    customer = models.ForeignKey(StripeCustomer, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True, null=True)  # Track invoices
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.plan.name}"


class PaymentMethod(models.Model):
    """
    Stores payment method details
    """
    customer = models.ForeignKey(StripeCustomer, on_delete=models.CASCADE)
    stripe_payment_method_id = models.CharField(max_length=255, unique=True)
    last_four = models.CharField(max_length=4)
    card_type = models.CharField(max_length=50)
    expiry_month = models.IntegerField()
    expiry_year = models.IntegerField()
    is_default = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_type} ending in {self.last_four}"
