# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Djangostripe.settings')

app = Celery('Djangostripe')

# Use a string here to avoid namespace conflicts
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
