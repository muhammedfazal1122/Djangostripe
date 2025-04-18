# Generated by Django 5.1.7 on 2025-04-08 07:21

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_metering', '0002_apimetering'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('beginner', 'Beginner'), ('pro', 'Pro')], max_length=50)),
                ('stripe_price_id', models.CharField(max_length=100)),
                ('base_api_calls', models.IntegerField(default=10)),
                ('overage_unit_amount', models.DecimalField(decimal_places=2, default=0.5, max_digits=6)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='apimetering',
            name='daily_reset',
        ),
        migrations.AddField(
            model_name='apimetering',
            name='billing_cycle_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='apimetering',
            name='last_reset_date',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_customer_id', models.CharField(blank=True, max_length=100, null=True)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('plan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='task_metering.subscriptionplan')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='metering_subscription', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='APIUsageBilling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('call_count', models.IntegerField(default=0)),
                ('overage_count', models.IntegerField(default=0)),
                ('billed_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('is_billed', models.BooleanField(default=False)),
                ('stripe_invoice_item_id', models.CharField(blank=True, max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metering_api_billing', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'date')},
            },
        ),
    ]
