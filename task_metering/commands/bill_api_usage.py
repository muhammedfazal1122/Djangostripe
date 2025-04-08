from django.core.management.base import BaseCommand
from django.utils import timezone
from task_metering.models import APIUsageBilling
import stripe

class Command(BaseCommand):
    help = 'Create Stripe invoice items for API usage overage'
    
    def handle(self, *args, **options):
        # Get unbilled usage records
        unbilled = APIUsageBilling.objects.filter(
            is_billed=False,
            overage_count__gt=0,
            billed_amount__gt=0
        )
        
        success_count = 0
        fail_count = 0
        
        for usage in unbilled:
            if usage.create_stripe_invoice_item():
                success_count += 1
            else:
                fail_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Created {success_count} invoice items, failed to create {fail_count}'
        ))
