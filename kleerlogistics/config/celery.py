"""
Celery configuration for KleerLogistics project.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('kleerlogistics')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Celery Beat Schedule
app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'users.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Every hour
    },
    'send-pending-notifications': {
        'task': 'notifications.tasks.send_pending_notifications',
        'schedule': 300.0,  # Every 5 minutes
    },
    'update-shipment-status': {
        'task': 'shipments.tasks.update_shipment_status',
        'schedule': 600.0,  # Every 10 minutes
    },
    'generate-analytics-reports': {
        'task': 'analytics.tasks.generate_daily_reports',
        'schedule': 86400.0,  # Daily
    },
} 