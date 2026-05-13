package com.playground.inventoryservice.api;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
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

    private final Counter reservationAttemptCounter;
    private final Counter reservationSuccessCounter;
    private final Counter duplicateEventCounter;
    private final Counter idempotencyConflictCounter;
    private final Set<String> processedEventIds = ConcurrentHashMap.newKeySet();
    private final Set<String> reservedOrderIds = ConcurrentHashMap.newKeySet();
    private final KafkaFailureSimulationProperties failureSimulationProperties;

    public InventoryEventHandler(MeterRegistry meterRegistry, KafkaFailureSimulationProperties failureSimulationProperties) {
        this.reservationAttemptCounter = meterRegistry.counter("inventory.reservation.attempts");
        this.reservationSuccessCounter = meterRegistry.counter("inventory.reservation.success");
        this.duplicateEventCounter = meterRegistry.counter("inventory.events.duplicates");
        this.idempotencyConflictCounter = meterRegistry.counter("inventory.events.idempotency_conflict");
        this.failureSimulationProperties = failureSimulationProperties;
    }

    @KafkaListener(topics = "${app.kafka.topics.order-created}", groupId = "${spring.kafka.consumer.group-id}")
    public void onOrderCreated(
            Map<String, Object> event,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            @Header(value = KafkaHeaders.RECEIVED_KEY, required = false) String key,
            @Header(value = "correlation_id", required = false) String correlationIdHeader,
            @Header(value = "traceparent", required = false) String traceparentHeader
    ) {
        reservationAttemptCounter.increment();

        String eventId = asString(event.get("eventId"));
        String orderId = asString(event.get("orderId"));
        String correlationId = correlationIdHeader != null ? correlationIdHeader : asString(event.get("correlation_id"));
        String traceId = asString(event.get("trace_id"));
        String scenario = asString(event.get("failureScenario"));

        withContext(correlationId, traceId);
        log.info("operation=kafka_event_consumed topic={} partition={} offset={} key={} event_id={} order_id={} correlation_id={} trace_id={} traceparent={}",
                topic, partition, offset, key, eventId, orderId, correlationId, traceId, traceparentHeader);

        try {
            if ("deserialization-error".equalsIgnoreCase(scenario)) {
                throw new IllegalArgumentException("Simulated deserialization error during processing");
            }

            if (eventId != null && !processedEventIds.add(eventId)) {
                duplicateEventCounter.increment();
                log.warn("operation=kafka_processing_failed event_id=duplicate_event topic={} partition={} offset={} key={} event_id={} order_id={}",
                        topic, partition, offset, key, eventId, orderId);
                return;
            }

            if (orderId != null && !reservedOrderIds.add(orderId)) {
                idempotencyConflictCounter.increment();
                log.warn("operation=kafka_processing_failed event_id=idempotency_conflict topic={} partition={} offset={} key={} event_id={} order_id={}",
                        topic, partition, offset, key, eventId, orderId);
                return;
            }

            if (failureSimulationProperties.poisonMessageEnabled() || "poison-message".equalsIgnoreCase(scenario)) {
                throw new IllegalStateException("Simulated poison message");
            }

            if ("retry-storm".equalsIgnoreCase(scenario)) {
                throw new RuntimeException("Simulated retry storm trigger");
            }

            if (failureSimulationProperties.processingDelayMs() > 0 || "processing-delay".equalsIgnoreCase(scenario)) {
                long delayMs = failureSimulationProperties.processingDelayMs() > 0 ? failureSimulationProperties.processingDelayMs() : 10_000;
                Thread.sleep(delayMs);
            }

            reservationSuccessCounter.increment();
            log.info("operation=order_persisted event_id=inventory_reserved topic={} partition={} offset={} key={} event_id={} order_id={}",
                    topic, partition, offset, key, eventId, orderId);
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
