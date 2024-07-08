# your_project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_bot.settings')

app = Celery('celery_app')
app.conf.update(
    result_backend='django-db',
    include=['pipeline.tasks', ],
    pool="solo",
)
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
