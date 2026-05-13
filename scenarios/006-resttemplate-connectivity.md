# 006 - RestTemplate Connectivity Failure

## Intent
Ensure AI agent can resolve service-to-service connectivity issues.

## Trigger
1. Break DNS or target URL for a downstream service.
2. Execute order flow through gateway.

## Expected User Symptom
- Immediate request failures for affected operation.

## Expected Telemetry
- Connection refused/unknown host exceptions.
- Error spans localized to failing client call.

## Root Cause
Incorrect downstream endpoint resolution for RestTemplate HTTP dependency.
