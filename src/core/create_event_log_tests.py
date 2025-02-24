import json
from collections.abc import Generator
from unittest import mock
from unittest.mock import ANY, MagicMock

import pytest
from clickhouse_connect.driver import Client
from core.enums import EventOutboxStatus
from core.models import EventOutbox
from core.tasks import process_event_outbox
from django.conf import settings

pytestmark = [pytest.mark.django_db]


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    yield


@pytest.fixture(autouse=True)
def f_clean_up_event_outbox() -> Generator:
    EventOutbox.objects.all().delete()
    yield


@pytest.fixture()
def f_mock_event_log_client() -> MagicMock:
    """Mock EventLogClient with a mocked ClickHouse client."""
    mock_client = mock.MagicMock()

    with mock.patch("core.tasks.EventLogClient.init", return_value=mock_client):
        yield mock_client


@pytest.fixture()
def f_event_outbox_entries() -> list[EventOutbox]:
    """Создание тестовых записей EventOutbox."""
    return [
        EventOutbox.objects.create(
            event_type="test_event",
            event_date_time="2025-02-22T12:00:00Z",
            environment="Local",
            event_context=json.dumps({'name': 'test', 'email': 'test@test.com'}),
            metadata_version=1,
            status=EventOutboxStatus.PENDING,
        )
    ]


def test_event_log_entry_published(
    f_event_outbox_entries: list[EventOutbox],
    f_ch_client: Client,
) -> None:
    process_event_outbox()
    log = f_ch_client.query("SELECT * FROM default.event_log WHERE event_type = 'test_event'")

    assert log.result_rows == [
        (
            'test_event',
            ANY,
            'Local',
            '{"name": "test", "email": "test@test.com"}',
            1
        )
    ]

    assert EventOutbox.objects.all().values_list('status', flat=True).first() == EventOutboxStatus.PROCESSED


def test_process_event_outbox_failure(
    f_mock_event_log_client: MagicMock, f_event_outbox_entries: list[EventOutbox]
) -> None:
    """Test handling errors when sending to ClickHouse fails."""
    f_mock_event_log_client.__enter__.return_value = f_mock_event_log_client
    f_mock_event_log_client.insert.side_effect = Exception("ClickHouse error")

    process_event_outbox()

    assert (
        EventOutbox.objects.filter(status=EventOutboxStatus.FAILED).count()
        == len(f_event_outbox_entries)
    )
