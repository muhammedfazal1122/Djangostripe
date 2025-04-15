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
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User

class SubscriptionPlansView(APIView):
    """📦 View available subscription plans"""
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
        
        print(f"📡 {request.user.username} fetched subscription plans.")
        return Response(data)


class CreateCheckoutSessionView(APIView):
    """🛒 Create a Stripe checkout session for subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):  
        plan_id = request.data.get('plan_id')
        print(f"📥 Received checkout session request from {request.user.username} for plan_id={plan_id}")
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            print(f"✅ Plan found: {plan.name} (${plan.overage_unit_amount})")

            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': plan, 'is_active': True}
            )
            
            if not subscription.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=f"{request.user.first_name} {request.user.last_name}",
                    metadata={'user_id': request.user.id}
                )
                subscription.stripe_customer_id = customer.id
                subscription.save()
                print(f"🧾 Created new Stripe customer: {customer.id}")
            else:
                print(f"👤 Existing Stripe customer ID: {subscription.stripe_customer_id}")
            
            try:
                price = stripe.Price.retrieve(plan.stripe_price_id)
                is_metered = hasattr(price.recurring, 'usage_type') and price.recurring.usage_type == 'metered'
                
                line_item = {'price': plan.stripe_price_id}
                if not is_metered:
                    line_item['quantity'] = 1
                
                print(f"🔍 Stripe Price Info → Metered: {is_metered}, Line Item: {line_item}")

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

                print(f"✅ Checkout Session Created: {checkout_session.id}")
                return Response({'checkout_url': checkout_session.url})
                
            except stripe.error.StripeError as se:
                print(f"❌ Stripe error: {str(se)}")
                return Response({'error': f"Stripe error: {str(se)}"}, status=status.HTTP_400_BAD_REQUEST)
            
        except SubscriptionPlan.DoesNotExist:
            print("🚫 Plan not found.")
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CancelSubscriptionView(APIView):
    """🛑 Cancel the user's current subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print(f"🧾 {request.user.username} is attempting to cancel subscription.")
        print(f"🧾 {request.user.is_active} is attempting to cancel is_active.")
        
        try:
            subscription = UserSubscription.objects.get(user=request.user, is_active=True)
            print(f"📜 Found active subscription: {subscription}")
            print(f"📜 Found active subscription: {subscription.stripe_subscription_id}")

            if not subscription.stripe_subscription_id:
                print("⚠️ No active Stripe subscription ID found.")
                return Response({"error": "No active subscription found"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                canceled_subscription = stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.is_active = False
                subscription.save()

                effective_date = datetime.fromtimestamp(
                    canceled_subscription.canceled_at
                ).strftime('%Y-%m-%d') if hasattr(canceled_subscription, 'canceled_at') else "immediate"

                print(f"❎ Subscription canceled: {subscription.stripe_subscription_id} → Effective: {effective_date}")
                
                return Response({
                    "status": "canceled",
                    "message": "Your subscription has been canceled",
                    "effective_date": effective_date
                })
                
            except stripe.error.StripeError as e:
                print(f"❌ Stripe error while canceling: {str(e)}")
                return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                
        except UserSubscription.DoesNotExist:
            print("🚫 User subscription record not found.")
            return Response({"error": "You don't have an active subscription"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateSubscriptionView(APIView):
    """🔄 Update the user's subscription to a different plan"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        plan_id = request.data.get('plan_id')
        print(f"🔁 Update request from {request.user.username} to plan ID: {plan_id}")
        
        if not plan_id:
            return Response({"error": "Plan ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            new_plan = SubscriptionPlan.objects.get(id=plan_id)
            print(f"🆕 Switching to plan: {new_plan.name}")

            subscription = UserSubscription.objects.get(user=request.user, is_active=True)

            if not subscription.stripe_subscription_id:
                return Response({"error": "No active subscription found"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                sub_data = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                item_id = sub_data['items']['data'][0]['id']

                updated_subscription = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': item_id,
                        'price': new_plan.stripe_price_id,
                    }],
                    proration_behavior='create_prorations',
                )

                subscription.plan = new_plan
                subscription.save()

                print(f"✅ Subscription updated → New Plan: {new_plan.name}")

                return Response({
                    "status": "updated",
                    "message": f"Your subscription has been updated to {new_plan.name}",
                    "effective_date": datetime.fromtimestamp(updated_subscription.current_period_start).strftime('%Y-%m-%d')
                })

            except stripe.error.StripeError as e:
                print(f"❌ Stripe error during update: {str(e)}")
                return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                
        except SubscriptionPlan.DoesNotExist:
            print("🚫 New plan not found.")
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)
        except UserSubscription.DoesNotExist:
            print("❌ Active user subscription not found.")
            return Response({"error": "You don't have an active subscription"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
                print("event['type'] Checkout session completed")
                self._handle_checkout_completed(event)
            elif event['type'] == 'customer.subscription.created':
                print("event['type'] Subscription created")
                self._handle_subscription_created(event)
            elif event['type'] == 'customer.subscription.updated':
                print("event['type'] Subscription updated")
                self._handle_subscription_updated(event)
            elif event['type'] == 'customer.subscription.deleted':
                print("event['type'] Subscription deleted")
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
        print(f"Checkout session completed: {session['id']}")
        # Extract customer and subscription info
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')
        print(f"Subscription subscription_id:_____________ {subscription_id}")
        print(f"Subscription customer_id: {customer_id}")
        print(f"Subscription user_id: {user_id}")
        print(f"Subscription plan_id: {plan_id}")

        if subscription_id and user_id and plan_id:
            # Get the subscription details
            subscription = stripe.Subscription.retrieve(subscription_id)
            print(f"Subscription details: {subscription}")
            print(f"Subscription subscription_id==========: {subscription_id}")
            
            try:
                # First try to get the User and Plan objects
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
                print(f"User found)))))))))))): {user.username}")
                print(f"Plan found: {plan.name}")
                
                # Convert Unix timestamps to Python datetime objects
                from datetime import datetime
                current_period_start = datetime.fromtimestamp(subscription.current_period_start)
                current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                
                # Update or create the subscription
                user_sub, created = UserSubscription.objects.update_or_create(
                    user=user,
                    defaults={
                        'stripe_customer_id': customer_id,
                        'stripe_subscription_id': subscription_id,
                        'plan': plan,
                        'is_active': subscription.status == 'active',
                        'current_period_start': current_period_start,
                        'current_period_end': current_period_end
                    }
                )
                print(f"User subscription created/updated: {created} for user {user.username}")
                print(f"User subscription updated_______: {user_sub.stripe_subscription_id} for user {user.username}")
                
                # Reset API usage counters
                metering, created = APIMetering.objects.get_or_create(user=user)
                metering.billing_cycle_count = 0
                metering.save()
                
                print(f"Subscription activated for user {user.username} on plan {plan.name},-----------------{metering.billing_cycle_count}")
                return Response({'status': 'success'})
                
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
                print(f"Subscription created: {subscription['id']} for user {user_sub.user.username}")  
                user_sub.plan_id = plan_id
                user_sub.is_active = subscription['status'] == 'active'
                
                # Convert Unix timestamps to datetime objects
                from datetime import datetime
                user_sub.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
                user_sub.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
                
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
            print(f"Subscription updated: {subscription['id']}")
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription['id'])
            
            # Update status, dates, and metadata
            user_sub.is_active = subscription['status'] == 'active'
            user_sub.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
            user_sub.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
            
            # Check if the price/plan has changed
            stripe_price_id = subscription['items']['data'][0]['price']['id']
            try:
                # Find the plan that matches this price ID
                new_plan = SubscriptionPlan.objects.get(stripe_price_id=stripe_price_id)
                if user_sub.plan != new_plan:
                    print(f"Plan changed from {user_sub.plan.name if user_sub.plan else 'None'} to {new_plan.name}")
                    user_sub.plan = new_plan
            except SubscriptionPlan.DoesNotExist:
                print(f"Warning: No plan found for Stripe price ID {stripe_price_id}")
            
            user_sub.save()
            
            # Reset API usage counters on plan change
            metering, created = APIMetering.objects.get_or_create(user=user_sub.user)
            metering.billing_cycle_count = 0
            metering.save()
            
        except UserSubscription.DoesNotExist:
            print(f"Could not find subscription with ID {subscription['id']}")

    # Update the _handle_subscription_deleted method:
    def _handle_subscription_deleted(self, event):
        subscription = event['data']['object']
        try:
            print(f"Subscription deleted: {subscription['id']}")
            user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription['id'])
            user_sub.is_active = False
            user_sub.save()
            
            # You may want to notify the user or perform cleanup actions here
            print(f"User {user_sub.user.username}'s subscription has been canceled")
        except UserSubscription.DoesNotExist:
            print(f"Could not find subscription with ID {subscription['id']}")
    
    def _handle_invoice_payment_succeeded(self, event):
        invoice = event['data']['object']
        # Reset billing cycle usage when payment succeeds
        try:
            print(f"Invoice payment succeeded: {invoice['id']}")
            user_sub = UserSubscription.objects.get(stripe_customer_id=invoice['customer'])
            metering, created = APIMetering.objects.get_or_create(user=user_sub.user)
            metering.billing_cycle_count = 0
            metering.save()
        except UserSubscription.DoesNotExist:
            pass

class UserSubscriptionStatusView(APIView):
    """Get current user's subscription status"""
    permission_classes = [IsAuthenticated]
    # throttle_classes = [SubscriptionBasedThrottle]
    
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
    # throttle_classes = [SubscriptionBasedThrottle]
    
    def get(self, request):
        print(f"📋 {request.user} requested task list.")
        print(f"📋 {request.user.username} requested task list.")
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
    # throttle_classes = [SubscriptionBasedThrottle]
    
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
    # throttle_classes = [SubscriptionBasedThrottle]
    
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
    



class UserAPIUsageView(APIView):
    """View current user's API usage metrics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            metering = APIMetering.objects.get(user=request.user)
            
            # Get user's subscription details
            try:
                subscription = UserSubscription.objects.get(user=request.user)
                plan_name = subscription.plan.name if subscription.plan else "No Plan"
                is_active = subscription.is_active
                if subscription.plan:
                    limit = subscription.plan.base_api_calls
                    remaining = max(0, limit - metering.daily_count)
                else:
                    limit = 0
                    remaining = 0
            except UserSubscription.DoesNotExist:
                plan_name = "No Subscription"
                is_active = False
                limit = 0
                remaining = 0
                
            # Get today's billing data
            today = date.today()
            try:
                billing = APIUsageBilling.objects.get(user=request.user, date=today)
                today_calls = billing.call_count
                today_overage = billing.overage_count
                today_amount = float(billing.billed_amount)
            except APIUsageBilling.DoesNotExist:
                today_calls = 0
                today_overage = 0
                today_amount = 0.0
                
            usage_data = {
                'plan': {
                    'name': plan_name,
                    'active': is_active,
                    'daily_limit': limit,
                    'remaining': remaining,
                },
                'usage': {
                    'today': metering.daily_count,
                    'billing_cycle': metering.billing_cycle_count,
                    'total': metering.total_count,
                    'methods': {
                        'get': metering.get_count,
                        'post': metering.post_count,
                        'put': metering.put_count,
                        'delete': metering.delete_count
                    },
                    'last_request': metering.last_request
                },
                'billing': {
                    'today_calls': today_calls,
                    'today_overage': today_overage,
                    'today_amount': f"${today_amount:.2f}"
                }
            }
            
            return Response(usage_data)
            
        except APIMetering.DoesNotExist:
            return Response({
                'message': 'No API usage recorded yet'
            })

class AdminAPIUsageView(APIView):
    """View API usage metrics for all users (admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        # Get optional username filter
        username = request.query_params.get('username', None)
        
        if username:
            users = User.objects.filter(username=username)
        else:
            users = User.objects.filter(is_active=True)
        
        # Collect usage data for each user
        usage_data = []
        for user in users:
            try:
                metering = APIMetering.objects.get(user=user)
                try:
                    subscription = UserSubscription.objects.get(user=user)
                    plan_name = subscription.plan.name if subscription.plan else "No Plan"
                    is_active = subscription.is_active
                except UserSubscription.DoesNotExist:
                    plan_name = "No Subscription"
                    is_active = False
                
                # Get today's billing
                today = date.today()
                try:
                    today_usage = APIUsageBilling.objects.get(user=user, date=today)
                    today_calls = today_usage.call_count
                    today_overage = today_usage.overage_count
                    today_billed = float(today_usage.billed_amount)
                except APIUsageBilling.DoesNotExist:
                    today_calls = 0
                    today_overage = 0
                    today_billed = 0.0
                
                # Add user data
                usage_data.append({
                    'username': user.username,
                    'email': user.email,
                    'plan': plan_name,
                    'subscription_active': is_active,
                    'api_usage': {
                        'daily': metering.daily_count,
                        'total': metering.total_count,
                        'billing_cycle': metering.billing_cycle_count,
                        'by_method': {
                            'get': metering.get_count,
                            'post': metering.post_count,
                            'put': metering.put_count,
                            'delete': metering.delete_count
                        },
                        'last_request': metering.last_request
                    },
                    'today_billing': {
                        'calls': today_calls,
                        'overage': today_overage,
                        'billed': f"${today_billed:.2f}"
                    }
                })
            except APIMetering.DoesNotExist:
                usage_data.append({
                    'username': user.username,
                    'email': user.email,
                    'plan': "No Data",
                    'subscription_active': False,
                    'api_usage': "No API usage recorded"
                })
        
        return Response(usage_data)