# 005 - Google Pub/Sub Publish Failure

## Intent
Exercise cloud messaging failure diagnosis (auth or endpoint misconfiguration).

## Trigger
1. Misconfigure credentials or topic.
2. Attempt publish from notification/audit integration path.

## Expected User Symptom
- Async side effects missing despite successful synchronous flow.

## Expected Telemetry
- Publish error counters spike.
- Retry/backoff logs with auth/not-found error codes.

## Root Cause
Invalid Pub/Sub configuration or credentials prevents successful publish.
