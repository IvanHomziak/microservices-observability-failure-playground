# 003 - Notification Backlog

## Intent
Confirm AI agent detects delayed async processing due to notification backlog.

## Trigger
1. Publish high volume of notification events.
2. Constrain notification worker throughput.

## Expected User Symptom
- Delayed confirmation messages while core order flow succeeds.

## Expected Telemetry
- Queue lag growth metrics.
- Increased event age at consumer.
- Longer spans in async notification pipeline.

## Root Cause
Notification consumer throughput below incoming event rate.
