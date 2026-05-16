# Readiness checklist

## Purpose
This checklist gives a deterministic, honest readiness gate for local runtime, scenario verification, and documentation consistency.

## Required tools
- Docker
- Docker Compose v2
- Java 21
- Maven
- curl
- bash

## Required free ports
- 3000
- 5432
- 8080–8085
- 9090
- 9092
- 3100
- 3200
- 4317
- 4318

## Static checks
Expected result: all commands exit `0`.

```bash
bash -n scripts/*.sh
```

## Docker Compose config checks
Expected result: all commands exit `0`.

```bash
docker compose config
docker compose -f docker-compose.yml -f docker-compose.s001.yml config
docker compose -f docker-compose.yml -f docker-compose.s002.yml config
docker compose -f docker-compose.yml -f docker-compose.kafka.yml --profile kafka config
docker compose -f docker-compose.yml -f docker-compose.notification.yml --profile async config
docker compose -f docker-compose.yml -f docker-compose.audit.yml --profile async config
```

## Maven test checks
Expected result: each service test suite exits `0`.

```bash
for service in api-gateway orders-service payments-service inventory-service notification-service audit-service; do
  if [ -f "$service/pom.xml" ]; then
    (cd "$service" && mvn test)
  fi
done
```

## Runtime scenario checks
Expected result: each verifier exits `0`.

Scenarios without verifier scripts must not be considered fully implemented. They should remain Partially implemented or Placeholder until a deterministic verifier is added.

```bash
./scripts/verify-milestone-1.sh
./scripts/verify-s001-resttemplate-timeout.sh
./scripts/verify-s002-payments-http-500.sh
./scripts/verify-kafka-flow.sh
./scripts/verify-notification-flow.sh
./scripts/verify-audit-flow.sh
./scripts/verify-observability-stack.sh
./scripts/verify-readiness.sh
```

## Troubleshooting
- If health checks fail, run: `docker compose logs --tail=200`
- If ports conflict, stop local processes or run: `docker compose down --remove-orphans`
- If stale config is suspected, recreate containers: `docker compose up -d --build --force-recreate`

## Cleanup commands
```bash
docker compose down --remove-orphans

docker compose -f docker-compose.yml -f docker-compose.s001.yml down --remove-orphans
docker compose -f docker-compose.yml -f docker-compose.s002.yml down --remove-orphans
docker compose -f docker-compose.yml -f docker-compose.kafka.yml --profile kafka down --remove-orphans
docker compose -f docker-compose.yml -f docker-compose.notification.yml --profile async down --remove-orphans
docker compose -f docker-compose.yml -f docker-compose.audit.yml --profile async down --remove-orphans
docker compose --profile observability down --remove-orphans
```
