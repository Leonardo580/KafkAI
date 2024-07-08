import time
from celery import shared_task
from .models import PipelineProgress, Pipeline
from django.db import transaction
import logging
from knowledge_base.ChatBot import RAGRetriever
logger = logging.getLogger(__name__)

@shared_task
def launch_pipeline_task(progress_id):
    progress = PipelineProgress.objects.get(pk=progress_id)
    pipeline_id = progress.pipeline.pk  # Store the ID, not the object
    try:
        def progress_callback(current, total):
            percentage = int((current / total) * 100)
            time.sleep(0.01)
            print(f'Progress: {percentage}%')
            progress.progress = percentage
            progress.save()

        bot = RAGRetriever()
        bot.embed_knowledge(progress.pipeline.knowledge, progress_callback)

        progress.status = 'completed'
        with transaction.atomic():  # Ensure the transaction is managed
            pipeline = Pipeline.objects.select_for_update().get(pk=pipeline_id)  # Lock the row for update
            pipeline.is_active = True
            pipeline.save()

    except Exception as e:
        progress.status = 'failed'
    finally:
        progress.save()
