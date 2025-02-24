from django.db import models
from django.utils import timezone
from core.enums import EventOutboxStatus


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None,  # noqa
    ) -> None:
        # https://docs.djangoproject.com/en/5.1/ref/models/fields/#django.db.models.DateField.auto_now
        self.updated_at = timezone.now()

        if isinstance(update_fields, list):
            update_fields.append('updated_at')
        elif isinstance(update_fields, set):
            update_fields.add('updated_at')

        super().save(force_insert, force_update, using, update_fields)


class EventOutbox(TimeStampedModel):
    event_type = models.CharField(max_length=255)
    event_date_time = models.DateTimeField(default=timezone.now)
    environment = models.CharField(max_length=50)
    event_context = models.JSONField()
    metadata_version = models.PositiveBigIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name.capitalize()) for status in EventOutboxStatus],
        default=EventOutboxStatus.PENDING,
        db_index=True,
    )

    def __str__(self):
        return f"{self.event_type} - {self.status} ({self.event_date_time})"

    class Meta:
        db_table = "event_outbox"
        app_label = "core"
