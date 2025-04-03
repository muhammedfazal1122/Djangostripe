from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from .models import StripeUser,StripePrice,PaymentMethod,Subscription,Colors,HookedUrl,ResetPassword



import stripe

import uuid
from email.mime.text import MIMEText
import requests

# Create your views here.


@csrf_exempt
def billing(request):
    if request.method == "POST":
        print("subscribe")

        plan = request.POST['plan']
        print(plan)

        if plan=="starter":
            obj_user=StripeUser.objects.get(name = request.user)
            price_obj = StripePrice.objects.get(name="starter")

            stripe_sub=stripe.Subscription.create(
                customer=obj_user.stripe_id,
                items=[
                    {"price": price_obj.stripe_id},
                ],
            )
            obj_user.stripe_subscription_id = stripe_sub.id
            obj_user.Subscription_active = True
            obj_user.price = "test_basic"
            obj_user.save()
            data = {"message":"success"}
            return JsonResponse(data)


    obj_user=StripeUser.objects.get(name = request.user)
    subscription_active = obj_user.Subscription_active
    print(subscription_active)
    content = {
        "active" : subscription_active,
    }
    if subscription_active==True:
        price = obj_user.price
        if price == "initiate":
            price_name = "Initiate"
            discription = "2 simultaneous AI engines, 100 free conversations every month"
        elif price == "accelerate":
            price_name="Accelerate"
            discription = "2 simultaneous AI engines, 1000 free conversations every month"
        elif price == "corporate":
            price_name = "Corporate"
            discription = "6 simultaneous AI engines, 5000 free conversations every month"
        elif price == "titans":
            price_name="Titans"
            discription = "As many simultaneous AI engines as required, 100,000 free conversations every month"
        else :
            price_name="None"
            discription = "plan expired"
        content['price_name']=price_name
        content['discription']=discription

    if subscription_active==False:
        card_created = obj_user.card_created
        return render(request,'payment/plan.html', {"card_created":card_created})
    else:
        return render(request,'payment/billing.html',content)
    