"""
Celery タスクキューの初期化
"""

import gc
import logging

from celery import Celery
from celery.signals import task_postrun

from settings import settings

logger = logging.getLogger(__name__)

app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
)

app.conf.timezone = settings.tz
app.conf.result_backend = settings.celery_result_backend
app.conf.task_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_serializer = "json"
app.conf.broker_connection_retry_on_startup = True
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 5
app.conf.worker_max_memory_per_child = 400_000
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

if settings.rabbitmq_use_tls:
    app.conf.broker_use_ssl = {
        "ssl_cert_reqs": "CERT_REQUIRED",
    }


@task_postrun.connect
def task_postrun_handler(sender=None, **kwargs):
    gc.collect()


logger.info(
    f"Celery initialized with broker: {settings.rabbitmq_host}:{settings.rabbitmq_port}"
)
