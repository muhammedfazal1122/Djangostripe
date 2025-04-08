from django.contrib import admin
from django.utils import timezone
from .models import (
    SubscriptionPlan, 
    UserSubscription, 
    APIUsageBilling, 
    APIMetering,
    Task
)

# SubscriptionPlan Admin
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_api_calls', 'overage_unit_amount')
    search_fields = ('name',)

# UserSubscription Admin
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'current_period_end')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username', 'user__email', 'stripe_customer_id')
    readonly_fields = ('stripe_customer_id', 'stripe_subscription_id', 
                      'current_period_start', 'current_period_end')

# APIUsageBilling Admin
class APIUsageBillingAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'call_count', 'overage_count', 'billed_amount', 'is_billed')
    list_filter = ('date', 'is_billed')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('call_count', 'overage_count', 'billed_amount')
    actions = ['recalculate_overage']
    
    def recalculate_overage(self, request, queryset):
        for usage in queryset:
            usage.calculate_overage()
        self.message_user(request, f"Recalculated overage for {queryset.count()} records")
    recalculate_overage.short_description = "Recalculate overage charges"

# APIMetering Admin
class APIMetricsAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_count', 'total_count', 'last_reset_date', 'last_request')
    readonly_fields = ('get_count', 'post_count', 'put_count', 'delete_count', 
                      'total_count', 'daily_count', 'billing_cycle_count',
                      'last_request', 'last_reset_date')
    search_fields = ('user__username', 'user__email')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')

# Task Admin
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description', 'user__username')

# Register all models
admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(APIUsageBilling, APIUsageBillingAdmin)
admin.site.register(APIMetering, APIMetricsAdmin)
admin.site.register(Task, TaskAdmin)