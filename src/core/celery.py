from django.conf import settings

from celery import Celery

app = Celery("core")

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.beat_schedule = settings.CELERY_BEAT_SCHEDULE

app.autodiscover_tasks()
