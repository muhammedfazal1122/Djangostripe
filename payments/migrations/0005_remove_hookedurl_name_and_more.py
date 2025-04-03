# Generated by Django 5.1.7 on 2025-04-02 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_stripecustomer_subscription_active_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hookedurl',
            name='name',
        ),
        migrations.RemoveField(
            model_name='paymentmethodnuropidea',
            name='user',
        ),
        migrations.DeleteModel(
            name='StripePriceNuropidea',
        ),
        migrations.RemoveField(
            model_name='stripeusernuropidea',
            name='name',
        ),
        migrations.RemoveField(
            model_name='subscriptionnuropidea',
            name='user',
        ),
        migrations.RemoveField(
            model_name='stripecustomer',
            name='Subscription_active',
        ),
        migrations.RemoveField(
            model_name='stripecustomer',
            name='card_created',
        ),
        migrations.RemoveField(
            model_name='stripecustomer',
            name='mail_key',
        ),
        migrations.RemoveField(
            model_name='stripecustomer',
            name='mail_validated',
        ),
        migrations.RemoveField(
            model_name='stripecustomer',
            name='price',
        ),
        migrations.RemoveField(
            model_name='stripecustomer',
            name='stripe_id',
        ),
        migrations.RemoveField(
            model_name='stripecustomer',
            name='stripe_subscription_id',
        ),
        migrations.AddField(
            model_name='subscription',
            name='stripe_invoice_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name='HookedUrl',
        ),
        migrations.DeleteModel(
            name='PaymentMethodNuropidea',
        ),
        migrations.DeleteModel(
            name='StripeUserNuropidea',
        ),
        migrations.DeleteModel(
            name='SubscriptionNuropidea',
        ),
    ]
