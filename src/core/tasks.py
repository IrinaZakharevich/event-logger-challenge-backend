import structlog
import os
from django.db import transaction

from celery import shared_task
from .enums import EventOutboxStatus
from .event_log_client import EventLogClient
from .models import EventOutbox

logger = structlog.get_logger(__name__)

BATCH_SIZE = int(os.getenv("CH_OUTBOX_BATCH_SIZE", 1000))


@shared_task
def process_event_outbox():
    """Обрабатывает записи в EventOutbox и отправляет в ClickHouse."""

    event_ids = (
        EventOutbox.objects.filter(status__in=[EventOutboxStatus.PENDING,EventOutboxStatus.FAILED])
        .order_by("event_date_time")
        .values_list("id", flat=True)[:BATCH_SIZE]
    )

    if not event_ids:
        return

    with transaction.atomic():
        events = EventOutbox.objects.select_for_update(skip_locked=True).filter(id__in=event_ids)

        if not events:
            return

        try:
            with EventLogClient.init() as client:
                client.insert(events)
            events.update(status=EventOutboxStatus.PROCESSED)
            logger.info("Processed %s events", len(events))

        except Exception as e:
            logger.error("Failed to insert events into ClickHouse", error=str(e))
            events.update(status=EventOutboxStatus.FAILED)
