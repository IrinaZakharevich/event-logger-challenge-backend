# Documentation for the Solution

## Introduction

As part of the test task, a mechanism for logging events into ClickHouse using the transactional outbox pattern has been implemented. The solution aims to address issues related to event loss, network errors, and high load on ClickHouse due to the large number of row-level records.

## Architectural Solution

### Key Changes
1. **A table `event_outbox` has been added to PostgreSQL** for temporarily storing events before they are sent to ClickHouse.
2. **A Celery task has been implemented**, which periodically collects events from `event_outbox` and sends them to ClickHouse in batches.
3. **Transactional integrity is guaranteed**: events are written to `event_outbox` as part of the main business logic, which prevents their loss in case of failures.
4. **Structured logging (structlog) has been used**, and integration with Sentry is provided for monitoring and debugging.

### Event Processing Flow
1. **Event Creation**: When an event occurs, it is saved to `event_outbox` in PostgreSQL.
2. **Background Processing**: Celery periodically extracts events from `event_outbox`, groups them into batches of 1000, and sends them to ClickHouse.

### Structure of `event_outbox`

| Column           | Data Type    | Description                                    |
|------------------|--------------|------------------------------------------------|
| id               | BIGSERIAL    | Unique identifier                              |
| event_type       | VARCHAR(255) | Type of the event                              |
| event_date_time  | TIMESTAMP    | Date and time of the event                     |
| environment      | VARCHAR(50)  | Environment                                    |
| event_context    | JSONB        | Event data                                     |
| metadata_version | BIGINT       | Metadata schema version                        |
| status           | VARCHAR(20)  | Processing status (pending, processed, failed) |
| created_at       | TIMESTAMP    | Creation time                                  |
| updated_at       | TIMESTAMP    | Last update time                               |

### Celery Task for Sending Events to ClickHouse

- Selects events with the status `pending`, `failed`.
- Groups them into batches.
- Sends them to ClickHouse in a single SQL query.
- Upon success, updates the status of the events to `processed`.
- In case of an error, the status is updated to `failed`, and the failure information is logged.

## Project Setup and Launch

### 1. Launch via Docker
```sh
docker-compose up -d --build
```

### 2. Apply Migrations
```sh
docker-compose exec app python manage.py migrate
```

### 3. Launch Celery Workers:
```sh
docker-compose exec app celery -A core.celery worker --loglevel=info
```

### 4. Launch Celery-Beat:
```sh
docker-compose exec app celery -A core.celery beat --loglevel=info
```

## Logging and Monitoring
- **Structlog** is used for formatted logging.
- You can add monitoring failed events by configuring alerts or periodic checks for events with the failed status. This can be done through Sentry or custom monitoring solutions that track the status of events and notify administrators in case of repeated failures or unexpected issues.

## Testing

### Run all tests
```sh
docker compose run --rm app pytest -svv
```

## Conclusion
This solution addresses data loss issues, improves ClickHouse performance, and makes log processing transactionally safe. Celery provides reliable background event processing, while structured logging helps in monitoring the system's operation.
You can monitor failed events by configuring alerts or periodic checks for events with the failed status. This can be done through Sentry or custom monitoring solutions that track the status of events and notify administrators in case of repeated failures or unexpected issues.