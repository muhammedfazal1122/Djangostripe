import stripe
import logging
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import StripeCustomer, SubscriptionPlan, Subscription, PaymentMethod

# Configure logging
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY



def register_view(request):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect('register')

        user = User.objects.create_user(username=email, first_name=full_name, email=email, password=password)
        user.save()
        messages.success(request, "Registration successful! You can log in now.")
        return redirect('login')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password!")

    return render(request, 'login.html')



def logout_view(request):
    logout(request)
    return redirect('login')


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')


    return render(request, 'home.html', {'user': request.user})



def billing_success(request):
    session_id = request.GET.get("session_id")

    try:
        # Retrieve checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Get the subscription ID from Stripe session
        stripe_subscription_id = checkout_session.subscription

        # Retrieve the subscription from Stripe
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        # Fetch the customer and plan
        stripe_customer = StripeCustomer.objects.get(stripe_customer_id=checkout_session.customer)
        plan = SubscriptionPlan.objects.get(stripe_price_id=stripe_subscription.items.data[0].price.id)

        # Store subscription in the database
        Subscription.objects.create(
            customer=stripe_customer,
            plan=plan,
            stripe_subscription_id=stripe_subscription.id,
            stripe_invoice_id=stripe_subscription.latest_invoice,
            status=stripe_subscription.status,
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
        )

        messages.success(request, "Subscription successfully stored in the database.")
        return redirect('billing_dashboard')

    except stripe.error.StripeError as e:
        messages.error(request, f"Error retrieving subscription: {str(e)}")
        return redirect('subscription_plans')




def list_subscription_plans(request):
    """
    List available subscription plans
    """
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    return render(request, 'subscriptionplanspage.html', {'plans': plans})



def subscribe_to_plan(request, plan_id):
    """
    Subscribe user to a specific plan using Stripe Checkout
    """
    try:
        # Fetch the plan
        plan = SubscriptionPlan.objects.get(id=plan_id)

        if plan.price == 0:
            messages.success(request, "You have subscribed to the Free plan!")
            return redirect('subscription_plans')

        # Fetch or create Stripe customer
        stripe_customer, created = StripeCustomer.objects.get_or_create(
            user=request.user,
            defaults={'stripe_customer_id': stripe.Customer.create(email=request.user.email).id}
        )

        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            customer=stripe_customer.stripe_customer_id,
            line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
            success_url=request.build_absolute_uri(f'/billing/success/?session_id={{CHECKOUT_SESSION_ID}}'),
            cancel_url=request.build_absolute_uri('/plans/'),
        )

        return redirect(checkout_session.url)

    except SubscriptionPlan.DoesNotExist:
        messages.error(request, "Selected plan does not exist.")
        return redirect('subscription_plans')

    except stripe.error.StripeError as e:
        messages.error(request, f"Subscription failed: {str(e)}")
        return redirect('subscription_plans')



# def subscribe_to_plan(request, plan_id):
#     print('🔍 Request received for subscription:', request.user, 'Plan ID:', plan_id)
    
#     user = request.user

#     try:
#         plan = SubscriptionPlan.objects.get(id=plan_id)
#         print('✅ Plan found:', plan)

#         # Get or create Stripe customer
#         stripe_customer, created = StripeCustomer.objects.get_or_create(
#             user=user,
#             defaults={'stripe_customer_id': stripe.Customer.create(email=user.email).id}
#         )
#         print('✅ Stripe customer:', stripe_customer, '| Created:', created)

#         # Fetch Stripe customer to check payment method
#         stripe_customer_data = stripe.Customer.retrieve(stripe_customer.stripe_customer_id)
#         print('🔍 Stripe customer details:', stripe_customer_data)

    
#         # Create Stripe subscription
#         subscription = stripe.Subscription.create(
#             customer=stripe_customer.stripe_customer_id,
#             items=[{'price': plan.stripe_price_id}],
#             expand=["latest_invoice.payment_intent"],
#         )
#         print('✅ Subscription created on Stripe:', subscription)

#         # Store subscription in database
#         new_subscription = Subscription.objects.create(
#             customer=stripe_customer,
#             plan=plan,
#             stripe_subscription_id=subscription.id,
#             status=subscription.status,
#             current_period_start=subscription.current_period_start,
#             current_period_end=subscription.current_period_end
#         )
#         print('✅ Subscription saved in database:', new_subscription)

#         return JsonResponse({"message": "Subscription created", "subscription_id": new_subscription.id}, status=201)

#     except SubscriptionPlan.DoesNotExist:
#         print('❌ Error: Plan not found')
#         return JsonResponse({"error": "Plan not found"}, status=404)

#     except stripe.error.StripeError as e:
#         print('❌ Stripe error:', str(e))
#         return JsonResponse({"error": str(e)}, status=400)

#     except Exception as e:
#         print('❌ General error:', str(e))
#         return JsonResponse({"error": "An unexpected error occurred"}, status=500)





def update_subscription(request, subscription_id):
    if request.method == "PUT":
        new_plan_id = request.POST.get("new_plan_id")

        try:
            subscription = Subscription.objects.get(id=subscription_id, customer__user=request.user)
            new_plan = SubscriptionPlan.objects.get(id=new_plan_id)

            # Update the Stripe subscription
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{"id": subscription.stripe_subscription_id, "price": new_plan.stripe_price_id}],
            )

            # Update local database
            subscription.plan = new_plan
            subscription.save()

            return JsonResponse({"message": "Subscription updated successfully"}, status=200)

        except Subscription.DoesNotExist:
            return JsonResponse({"error": "Subscription not found"}, status=404)

        except SubscriptionPlan.DoesNotExist:
            return JsonResponse({"error": "New plan not found"}, status=404)

        except stripe.error.StripeError as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)



def get_subscription(request, subscription_id):
    try:
        subscription = Subscription.objects.get(id=subscription_id, customer__user=request.user)
        data = {
            "id": subscription.id,
            "plan": subscription.plan.name,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
        }
        return JsonResponse(data, status=200)

    except Subscription.DoesNotExist:
        return JsonResponse({"error": "Subscription not found"}, status=404)





def cancel_subscription(request, subscription_id):
    if request.method == "DELETE":
        try:
            subscription = Subscription.objects.get(id=subscription_id, customer__user=request.user)

            # Cancel the subscription on Stripe
            stripe.Subscription.delete(subscription.stripe_subscription_id)

            # Update local database
            subscription.status = "canceled"
            subscription.save()

            return JsonResponse({"message": "Subscription canceled successfully"}, status=200)

        except Subscription.DoesNotExist:
            return JsonResponse({"error": "Subscription not found"}, status=404)

        except stripe.error.StripeError as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """

    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")
 
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    if event["type"] == "invoice.payment_succeeded":
        subscription_id = event["data"]["object"]["subscription"]
        Subscription.objects.filter(stripe_subscription_id=subscription_id).update(status="active")

    elif event["type"] == "customer.subscription.deleted":
        subscription_id = event["data"]["object"]["id"]
        Subscription.objects.filter(stripe_subscription_id=subscription_id).update(status="canceled")

    return JsonResponse({"message": "Webhook received"}, status=200)



def billing_dashboard(request):
    """
    User's billing dashboard
    Simplified version without authentication
    """
    # try:
    #     # Get the most recent subscription (for demonstration)
    #     active_subscription = Subscription.objects.filter(
    #         status='active'
    #     ).order_by('-subscribed_at').first()
        
    #     # Get recent payment methods
    #     payment_methods = PaymentMethod.objects.order_by('-added_at')[:5]
        
    #     context = {
    #         'active_subscription': active_subscription,
    #         'payment_methods': payment_methods
    #     }
    return render(request, 'task_page.html')
    


def add_payment_method(request):
    """
    Add a new payment method
    Simplified version without specific user context
    """
    if request.method == 'POST':
        try:
            # Create a generic Stripe customer for testing
            stripe_customer = stripe.Customer.create(
                email='test@example.com',
                name='Test User'
            )
            
            # Create payment method setup intent
            setup_intent = stripe.SetupIntent.create(
                customer=stripe_customer.id,
                payment_method_types=['card']
            )
            
            context = {
                'client_secret': setup_intent.client_secret,
                'stripe_public_key': settings.STRIPE_TEST_PUBLIC_KEY
            }
            return render(request, 'addpaymentmethod.html', context)
        
        except stripe.error.StripeError as e:
            logger.error(f"Payment Method Setup Error: {e}")
            messages.error(request, "Unable to set up payment method. Please try again.")
            return redirect('home')
    
    # Setup intent for GET request
    try:
        stripe_customer = stripe.Customer.create(
            email='test@example.com',
            name='Test User'
        )
        
        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer.id,
            payment_method_types=['card']
        )
        
        context = {
            'client_secret': setup_intent.client_secret,
            'stripe_public_key': settings.STRIPE_TEST_PUBLIC_KEY
        }
        return render(request, 'addpaymentmethod.html', context)
    
    except stripe.error.StripeError as e:
        logger.error(f"Payment Method Setup Error: {e}")
        messages.error(request, "Unable to set up payment method. Please try again.")
        return redirect('home')



