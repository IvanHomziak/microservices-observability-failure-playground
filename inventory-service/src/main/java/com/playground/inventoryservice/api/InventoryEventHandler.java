package com.playground.inventoryservice.api;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class InventoryEventHandler {

    private static final Logger log = LoggerFactory.getLogger(InventoryEventHandler.class);
    private final String serviceName;
    private final String environment;

    private final Counter reservationAttemptCounter;
    private final Counter reservationSuccessCounter;
    private final Counter duplicateEventCounter;
    private final Counter idempotencyConflictCounter;
    private final Set<String> processedEventIds = ConcurrentHashMap.newKeySet();
    private final Set<String> reservedOrderIds = ConcurrentHashMap.newKeySet();

    public InventoryEventHandler(MeterRegistry meterRegistry,
                                 @Value("${spring.application.name:inventory-service}") String serviceName,
                                 @Value("${app.environment:local}") String environment) {
        this.reservationAttemptCounter = meterRegistry.counter("inventory.reservation.attempts");
        this.reservationSuccessCounter = meterRegistry.counter("inventory.reservation.success");
        this.duplicateEventCounter = meterRegistry.counter("inventory.events.duplicates");
        this.idempotencyConflictCounter = meterRegistry.counter("inventory.events.idempotency_conflict");
        this.serviceName = serviceName;
        this.environment = environment;
    }

    @KafkaListener(topics = "${app.kafka.topics.order-created}", groupId = "${spring.kafka.consumer.group-id}")
    public void onOrderCreated(
            Map<String, Object> event,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            @Header(value = KafkaHeaders.RECEIVED_KEY, required = false) String key
    ) {
        reservationAttemptCounter.increment();

        String eventId = asString(event.get("eventId"));
        String orderId = asString(event.get("orderId"));
        String correlationId = asString(event.get("correlation_id"));
        String traceId = asString(event.get("trace_id"));
        String scenario = asString(event.get("failureScenario"));

        withContext(correlationId, traceId);
        log.info("event_id=kafka-event-consumed operation=kafka_event_consumed service={} environment={} topic={} partition={} offset={} key={} event_id={} order_id={} correlation_id={} trace_id={}",
                serviceName, environment, topic, partition, offset, key, eventId, orderId, correlationId, traceId);

        try {
            if ("deserialization-error".equalsIgnoreCase(scenario)) {
                throw new IllegalArgumentException("Simulated deserialization error during processing");
            }

            if (eventId != null && !processedEventIds.add(eventId)) {
                duplicateEventCounter.increment();
                log.warn("event_id=kafka-processing-failed operation=kafka_processing_failed service={} environment={} topic={} partition={} offset={} key={} event_id={} order_id={} exception_type={} exception_message={}",
                        serviceName, environment, topic, partition, offset, key, eventId, orderId, "DuplicateEvent", "Duplicate event detected");
                return;
            }

            if (orderId != null && !reservedOrderIds.add(orderId)) {
                idempotencyConflictCounter.increment();
                log.warn("event_id=kafka-processing-failed operation=kafka_processing_failed service={} environment={} topic={} partition={} offset={} key={} event_id={} order_id={} exception_type={} exception_message={}",
                        serviceName, environment, topic, partition, offset, key, eventId, orderId, "IdempotencyConflict", "Order already reserved");
                return;
            }

            if ("poison-message".equalsIgnoreCase(scenario)) {
                throw new IllegalStateException("Simulated poison message");
            }

            if ("retry-storm".equalsIgnoreCase(scenario)) {
                throw new RuntimeException("Simulated retry storm trigger");
            }

            if ("processing-delay".equalsIgnoreCase(scenario)) {
                Thread.sleep(10_000);
            }

            reservationSuccessCounter.increment();
            log.info("event_id=order-persisted operation=order_persisted service={} environment={} topic={} partition={} offset={} key={} event_id={} order_id={}",
                    serviceName, environment, topic, partition, offset, key, eventId, orderId);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Interrupted while simulating processing delay", e);
        } finally {
            MDC.remove("correlation_id");
            MDC.remove("trace_id");
        }
    }

    private static void withContext(String correlationId, String traceId) {
        if (correlationId != null && !correlationId.isBlank()) {
            MDC.put("correlation_id", correlationId);
        }
        if (traceId != null && !traceId.isBlank()) {
            MDC.put("trace_id", traceId);
        }
    }

    private static String asString(Object value) {
        return value == null ? null : String.valueOf(value);
    }
}
