# Generated by Django 5.1.7 on 2025-04-03 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apimetering',
            name='daily_limit',
            field=models.IntegerField(default=10),
        ),
        migrations.AddField(
            model_name='apimetering',
            name='total_limit',
            field=models.IntegerField(default=100),
        ),
    ]
