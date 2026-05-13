# Scripts

Helper scripts for running the playground and triggering deterministic scenarios.

## Usage

- `./scripts/run-local.sh` — start shared infrastructure via `docker compose up -d`.
- `./scripts/stop-local.sh` — stop shared infrastructure via `docker compose down`.
- `./scripts/trigger-successful-order.sh` — send a baseline successful order request.
- `./scripts/trigger-s001-resttemplate-timeout.sh` — trigger S001 timeout behavior.
- `./scripts/trigger-s002-payments-http-500.sh` — trigger S002 payments 500 behavior (requires payments failure mode enabled).
- `./scripts/show-logs-by-correlation-id.sh <correlation-id>` — filter service logs by correlation ID.
- `./scripts/show-logs-by-trace-id.sh <trace-id>` — filter service logs by trace ID.

Each trigger script prints:
- scenario ID
- request payload
- response
- correlation ID (if available)
- trace ID (if available)
- where to investigate in Grafana/Loki/Tempo
