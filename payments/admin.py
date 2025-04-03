from django.contrib import admin
from .models import SubscriptionPlan, StripeCustomer, Subscription

# Register your models here.
admin.site.register(SubscriptionPlan)
admin.site.register(StripeCustomer)
admin.site.register(Subscription)
