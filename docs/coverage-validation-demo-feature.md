# Coverage Validation Demo Feature (Positive Path)

This is a positive validation PR fixture that validates the green path for the Unit Test Coverage PR Agent.

## Scope

- Expected affected service: `orders-service`
- Expected production file: `orders-service/src/main/java/com/playground/ordersservice/app/OrderRiskClassifier.java`
- Expected related test file: `orders-service/src/test/java/com/playground/ordersservice/app/OrderRiskClassifierTest.java`
- Expected workflow: `Unit Test Coverage PR Agent`
- Expected result: `success`

## Expected artifacts

- `affected-services.txt`
- `changed-files.txt`
- `surefire-files.txt`
- `jacoco-files.txt`
- `unit-test-coverage-report.md`
- `unit-test-coverage-report.json`
- `unit-test-coverage-patch-proposal.md`
- `unit-test-coverage-patch-proposal.json`
- `pr-comment.md` (if enabled)

## Expected report

- `policy_violations = 0`
- `coverage_status = sufficient`
- `merge_recommendation = approve`
- related test evidence = `matched`
- mapping strategy = `exact_class_name` or high-confidence equivalent

## Expected workflow behavior

1. Detect affected services -> success
2. `affected-services.txt` contains `orders-service`
3. Run Maven verify for `orders-service` -> success
4. Generate Surefire XML -> success
5. Generate JaCoCo XML -> success
6. Generate coverage report -> success
7. Enforce coverage policy -> success
8. Upload artifacts -> success

## Expected JSON report assertions

- `changed_production_files` contains `OrderRiskClassifier.java`
- `changed_test_files` contains `OrderRiskClassifierTest.java`
- `changed_services` contains `orders-service`
- `test_execution_failures` is empty
- `test_failure_count = 0` (if field exists)
- `test_error_count = 0` (if field exists)
- `policy_violations` is empty
- `coverage_status` is `sufficient`
- `merge_recommendation` is `approve`
- `related_test_evidence.status` is `matched` (if field exists)
- `mapping_strategy` is `exact_class_name` or high-confidence equivalent (if field exists)
