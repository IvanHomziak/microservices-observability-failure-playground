# 002 - Inventory Consistency Failure

## Intent
Test diagnosis of stale inventory state causing oversell and compensation behavior.

## Trigger
1. Run concurrent order requests for low-stock SKU.
2. Delay inventory reservation confirmation path.

## Expected User Symptom
- Some orders accepted then later canceled.

## Expected Telemetry
- Spike in compensation/cancellation events.
- Trace branches showing race between reservation and confirmation.

## Root Cause
Non-atomic inventory reservation/commit path causing stale-read decisions under concurrency.
