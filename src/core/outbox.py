import re
from core.base_model import Model
from core.models import EventOutbox
from core.enums import EventOutboxStatus
from django.conf import settings
from django.utils import timezone


class EventOutboxService:
    @staticmethod
    def create(event: Model) -> None:
        EventOutbox.objects.create(
            event_type=EventOutboxService._to_snake_case(event.__class__.__name__),
            event_date_time=timezone.now(),
            event_context=event.model_dump_json(),
            environment=settings.ENVIRONMENT,
            status=EventOutboxStatus.PENDING,
        )

    @staticmethod
    def _to_snake_case(event_name: str) -> str:
        result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', event_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()
