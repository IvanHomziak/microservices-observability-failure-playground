# 004 - Kafka Consumer Lag / Poison Message

## Intent
Validate detection of Kafka lag and stuck consumer behavior.

## Trigger
1. Publish malformed message to audit topic.
2. Keep consumer retrying same message.

## Expected User Symptom
- Audit entries delayed or missing.

## Expected Telemetry
- Consumer lag increasing.
- Repeated exception logs for same record key/offset.
- Trace discontinuity after producer span.

## Root Cause
Poison message repeatedly failing deserialization/validation and blocking partition progress.
