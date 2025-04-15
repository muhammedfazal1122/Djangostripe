from django.contrib import admin
from django.utils.html import format_html
from .models import SubscriptionPlan, UserSubscription, APIMetering, APIUsageBilling, Task

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_api_calls', 'overage_unit_amount', 'stripe_price_id')
    search_fields = ('name',)

class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'stripe_customer_id', 'subscription_status')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username', 'user__email', 'stripe_customer_id')
    
    def subscription_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: red;">Inactive</span>')
    
    subscription_status.short_description = 'Status'

class APIMeteringAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_count', 'billing_cycle_count', 'total_count', 'last_request')
    list_filter = ('last_reset_date', 'last_request')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'daily_count', 'billing_cycle_count', 'total_count', 
                      'get_count', 'post_count', 'put_count', 'delete_count', 'last_request')

class APIUsageBillingAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'call_count', 'overage_count', 'billed_amount', 'is_billed')
    list_filter = ('date', 'is_billed')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'date', 'call_count', 'overage_count', 'billed_amount', 'is_billed')
    actions = ['create_stripe_invoice_items']
    
    def create_stripe_invoice_items(self, request, queryset):
        count = 0
        for record in queryset.filter(is_billed=False, overage_count__gt=0):
            if record.create_stripe_invoice_item():
                count += 1
        
        self.message_user(request, f"Created {count} Stripe invoice items")
    
    create_stripe_invoice_items.short_description = "Create Stripe invoice items for selected records"

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(APIMetering, APIMeteringAdmin)
admin.site.register(APIUsageBilling, APIUsageBillingAdmin)
admin.site.register(Task)