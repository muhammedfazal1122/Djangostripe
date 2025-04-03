# Generated by Django 5.1.7 on 2025-04-01 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_stripepricenuropidea_hookedurl_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripecustomer',
            name='Subscription_active',
            field=models.BooleanField(default='False'),
        ),
        migrations.AddField(
            model_name='stripecustomer',
            name='card_created',
            field=models.BooleanField(default='False'),
        ),
        migrations.AddField(
            model_name='stripecustomer',
            name='mail_key',
            field=models.CharField(blank=True, max_length=70, null=True),
        ),
        migrations.AddField(
            model_name='stripecustomer',
            name='mail_validated',
            field=models.BooleanField(default='False'),
        ),
        migrations.AddField(
            model_name='stripecustomer',
            name='price',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='stripecustomer',
            name='stripe_id',
            field=models.CharField(default=22, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stripecustomer',
            name='stripe_subscription_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
