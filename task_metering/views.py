# views.py - Add subscription management views
from datetime import date, datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
import stripe

from .serializers import TaskSerializer
from .models import SubscriptionPlan, Task, UserSubscription, APIMetering, APIUsageBilling
from .throttling import SubscriptionBasedThrottle

class SubscriptionPlansView(APIView):
    """View available subscription plans"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        data = [{
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'base_api_calls': plan.base_api_calls,
            'overage_cost': f"${float(plan.overage_unit_amount):.2f} per additional call"
        } for plan in plans]
        return Response(data)
    


class CreateCheckoutSessionView(APIView):
    """Create a Stripe checkout session for subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):  
        plan_id = request.data.get('plan_id')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Get or create customer
            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': None, 'is_active': False}
            )
            
            if not subscription.stripe_customer_id:
                # Create a new Stripe customer
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=f"{request.user.first_name} {request.user.last_name}",
                    metadata={'user_id': request.user.id}
                )
                subscription.stripe_customer_id = customer.id
                subscription.save()
            
            # Check if the price is metered
            try:
                price = stripe.Price.retrieve(plan.stripe_price_id)
                is_metered = hasattr(price.recurring, 'usage_type') and price.recurring.usage_type == 'metered'
                
                # Prepare line item without quantity by default
                line_item = {
                    'price': plan.stripe_price_id,
                }
                
                # Only add quantity for non-metered prices
                if not is_metered:
                    line_item['quantity'] = 1
                
                # For debugging
                print(f"Price ID: {plan.stripe_price_id}")
                print(f"Is metered: {is_metered}")
                print(f"Line item: {line_item}")
                
                # Create checkout session
                checkout_session = stripe.checkout.Session.create(
                    customer=subscription.stripe_customer_id,
                    payment_method_types=['card'], 
                    line_items=[line_item],
                    mode='subscription',
                    success_url=request.build_absolute_uri('/subscription/success/'),
                    cancel_url=request.build_absolute_uri('/subscription/cancel/'),
                    metadata={
                        'user_id': request.user.id,
                        'plan_id': plan.id
                    }
                )
                
                return Response({'checkout_url': checkout_session.url})
                
            except stripe.error.StripeError as se:
                return Response({'error': f"Stripe error: {str(se)}"}, status=status.HTTP_400_BAD_REQUEST)
            
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class SubscriptionWebhookView(APIView):
    """Handle Stripe webhooks for subscription events"""
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Handle subscription events
            if event['type'] == 'checkout.session.completed':
                self._handle_checkout_completed(event)
            elif event['type'] == 'customer.subscription.created':
                self._handle_subscription_created(event)
            elif event['type'] == 'customer.subscription.updated':
                self._handle_subscription_updated(event)
            elif event['type'] == 'customer.subscription.deleted':
                self._handle_subscription_deleted(event)
            # elif event['type'] == 'invoice.payment_succeeded':
            #     self._handle_invoice_payment_succeeded(event)
            
            return Response({'status': 'success'})
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def _handle_checkout_completed(self, event):
        session = event['data']['object']
        
        # Extract customer and subscription info
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')
        
        if subscription_id and user_id and plan_id:
            # Get the subscription details
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            try:
                # First try to get the User and Plan objects
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                # Update or create the subscription
                user_sub, created = UserSubscription.objects.update_or_create(
                    user=user,
                    defaults={
                        'stripe_customer_id': customer_id,
                        'stripe_subscription_id': subscription_id,
                        'plan': plan,
                        'is_active': subscription.status == 'active',
                        'current_period_start': subscription.current_period_start,
                        'current_period_end': subscription.current_period_end
                    }
                )
                
                # Reset API usage counters
                metering, created = APIMetering.objects.get_or_create(user=user)
                metering.billing_cycle_count = 0
                metering.save()
                
                print(f"Subscription activated for user {user.username} on plan {plan.name}")
                
            except (User.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
                print(f"Error handling checkout completion: {str(e)}")
    

    def _handle_subscription_created(self, event):
        subscription = event['data']['object']
        metadata = subscription.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')
        
        if user_id and plan_id:
            try:
                user_sub = UserSubscription.objects.get(stripe_customer_id=subscription['customer'])
                user_sub.stripe_subscription_id = subscription['id']
                user_sub.plan_id = plan_id
                user_sub.is_active = subscription['status'] == 'active'
                user_sub.current_period_start = subscription['current_period_start']
                user_sub.current_period_end = subscription['current_period_end']
                user_sub.save()
                
                # Reset API usage counters
                metering, created = APIMetering.objects.get_or_create(user=user_sub.user)
                metering.billing_cycle_count = 0
                metering.save()
                
            except UserSubscription.DoesNotExist:
                pass
    
    def _handle_subscription_updated(self, event):
        subscription = event['data']['object']
        try:
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription['id'])
            user_sub.is_active = subscription['status'] == 'active'
            user_sub.current_period_start = subscription['current_period_start']
            user_sub.current_period_end = subscription['current_period_end']
            user_sub.save()
        except UserSubscription.DoesNotExist:
            pass
    
    def _handle_subscription_deleted(self, event):
        subscription = event['data']['object']
        try:
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription['id'])
            user_sub.is_active = False
            user_sub.save()
        except UserSubscription.DoesNotExist:
            pass
    
    # def _handle_invoice_payment_succeeded(self, event):
    #     invoice = event['data']['object']
    #     # Reset billing cycle usage when payment succeeds
    #     try:
    #         user_sub = UserSubscription.objects.get(stripe_customer_id=invoice['customer'])
    #         metering, created = APIMetering.objects.get_or_create(user=user_sub.user)
    #         metering.billing_cycle_count = 0
    #         metering.save()
    #     except UserSubscription.DoesNotExist:
    #         pass

class UserSubscriptionStatusView(APIView):
    """Get current user's subscription status"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [SubscriptionBasedThrottle]
    
    def get(self, request):
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            metering = APIMetering.objects.get(user=request.user)
            
            # Get today's usage
            today = date.today()
            try:
                daily_usage = APIUsageBilling.objects.get(user=request.user, date=today)
            except APIUsageBilling.DoesNotExist:
                daily_usage = None
            
            data = {
                'subscription': {
                    'plan': subscription.plan.name if subscription.plan else None,
                    'is_active': subscription.is_active,
                    'api_call_limit': subscription.get_api_call_limit() if subscription.is_active else 0,
                },
                'api_usage': {
                    'today': metering.daily_count,
                    'total': metering.total_count,
                    'billing_cycle': metering.billing_cycle_count,
                },
                'billing': {
                    'todays_calls': daily_usage.call_count if daily_usage else 0,
                    'todays_overage': daily_usage.overage_count if daily_usage else 0,
                    'todays_charges': f"${float(daily_usage.billed_amount):.2f}" if daily_usage else "$0.00",
                },
                'remaining_calls': max(0, subscription.get_api_call_limit() - metering.daily_count) if subscription.is_active else 0
            }
            
            return Response(data)
        except UserSubscription.DoesNotExist:
            return Response({
                'subscription': None,
                'message': 'You do not have an active subscription'
            })

# Task API with subscription throttling 
class TaskListCreateView(APIView):
    """API: Get list of tasks & Create a task."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [SubscriptionBasedThrottle]
    
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskDetailView(APIView):
    """API: Retrieve, Update or Delete a specific task."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [SubscriptionBasedThrottle]
    
    def get_object(self, task_id, user):
        return get_object_or_404(Task, id=task_id, user=user)
    
    def get(self, request, task_id):
        task = self.get_object(task_id, request.user)
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def put(self, request, task_id):
        task = self.get_object(task_id, request.user)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, task_id):
        task = self.get_object(task_id, request.user)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class APIMetricsView(APIView):
    """API: View your API usage metrics."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [SubscriptionBasedThrottle]
    
    def get(self, request):
        metering, created = APIMetering.objects.get_or_create(user=request.user)
        
        # Display the current counter values
        data = {
            'username': request.user.username,
            'total_requests': metering.total_count,
            'daily_requests': metering.daily_count,
            'get_requests': metering.get_count,
            'post_requests': metering.post_count,
            'put_requests': metering.put_count,
            'delete_requests': metering.delete_count,
            'last_request': metering.last_request,
        }
        
        return Response(data)




class Successpage(APIView):
    """API: View your API usage metrics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({"message": "Success! Your subscription is active."})
    

