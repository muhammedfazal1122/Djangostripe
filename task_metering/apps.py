from django.apps import AppConfig

# task_metering/apps.py
class TaskMeteringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'task_metering'
    
    def ready(self):
        # Import signal handlers
        import task_metering.signals
