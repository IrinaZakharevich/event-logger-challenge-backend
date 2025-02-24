import uuid
from collections.abc import Generator
from unittest.mock import ANY

import pytest
from users.use_cases import CreateUser, CreateUserRequest, UserCreated

from core.models import EventOutbox

pytestmark = [pytest.mark.django_db]


@pytest.fixture()
def f_use_case() -> CreateUser:
    return CreateUser()


@pytest.fixture(autouse=True)
def f_clean_up_event_outbox() -> Generator:
    EventOutbox.objects.all().delete()
    yield


def test_user_created(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )

    response = f_use_case.execute(request)

    assert response.result.email == 'test@email.com'
    assert response.error == ''


def test_emails_are_unique(f_use_case: CreateUser) -> None:
    request = CreateUserRequest(
        email='test@email.com', first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)
    response = f_use_case.execute(request)

    assert response.result is None
    assert response.error == 'User with this email already exists'


def test_event_log_entry_published(
    f_use_case: CreateUser
) -> None:
    email = f'test_{uuid.uuid4()}@email.com'
    request = CreateUserRequest(
        email=email, first_name='Test', last_name='Testovich',
    )

    f_use_case.execute(request)
    log = list(EventOutbox.objects.all())
    log_data = [
        (entry.event_type, entry.event_date_time, entry.environment, entry.event_context, entry.metadata_version)
        for entry in log
    ]
    assert log_data[0] == (
        'user_created',
        ANY,
        'Local',
        UserCreated(email=email, first_name='Test', last_name='Testovich').model_dump_json(),
        1,
    )
