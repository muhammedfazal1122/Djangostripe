# Generated by Django 5.1.7 on 2025-04-11 06:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task_metering', '0004_subscriptionplan_is_metered_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscriptionplan',
            name='is_metered',
        ),
        migrations.RemoveField(
            model_name='usersubscription',
            name='stripe_subscription_item_id',
        ),
    ]
