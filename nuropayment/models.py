from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class ResetPassword(models.Model):
    name = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length = 70, null = True)    

class StripeUser(models.Model):
    name = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=50)
    card_created = models.BooleanField(default="False")
    Subscription_active = models.BooleanField(default="False")
    stripe_subscription_id = models.CharField(max_length=50, blank = True, null = True)
    price = models.CharField(max_length=50, blank=True, null=True)

    mail_key = models.CharField(max_length=70, null=True, blank=True)
    mail_validated = models.BooleanField(default="False")

class HookedUrl(models.Model):
    name = models.ForeignKey(User, on_delete=models.CASCADE)
    hook_url = models.URLField()
    #section_id = models.CharField(max_length=50, )

class StripePrice(models.Model):
    name = models.CharField(max_length=200)
    stripe_id = models.CharField(max_length=50)
    desc = models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.name+'_'+self.stripe_id

class PaymentMethod(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    number = models.CharField(max_length=4)
    exp_month = models.CharField(max_length=2)
    exp_year = models.CharField(max_length=5)
    stripe_id = models.CharField(max_length=50)


    def __str__(self):
        return self.number+'_'+self.stripe_id

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=50)

class Colors(models.Model):
    name = models.OneToOneField(User, on_delete=models.CASCADE)
    first_color = models.CharField(max_length=10, default="#9876E7")
    second_color = models.CharField(max_length=10, default="#5F80F9")


class Session(models.Model):

    name = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length = 14)
    end_email = models.EmailField(max_length = 50)
    end_username = models.CharField(max_length = 50)
    def __str__(self):
        return str(self.name)+'_'+self.session_id

class SessionChat(models.Model):

    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    user_text = models.CharField(max_length = 1000)
    bot_text = models.CharField(max_length = 1000)
    created_at = models.DateTimeField(auto_now_add = True)
    def __str__(self):
        return str(self.session_id)+'_'+str(self.created_at)

