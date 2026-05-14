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

import java.math.BigDecimal;
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
            OrderCreatedEvent event,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            @Header(value = "correlation_id", required = false) String correlationIdHeader,
            @Header(value = "traceparent", required = false) String traceparentHeader
    ) {
        reservationAttemptCounter.increment();

        String eventId = event.eventId();
        String orderId = event.orderId();
        String correlationId = correlationIdHeader != null ? correlationIdHeader : event.correlationId();
        String traceId = event.traceId();

        withContext(correlationId, traceId);
        log.info("operation=kafka_event_consumed topic={} partition={} offset={} event_id={} order_id={} correlation_id={} trace_id={} traceparent={}",
                topic, partition, offset, eventId, orderId, correlationId, traceId, traceparentHeader);

        try {
            validatePoisonMessage(event);

            if (eventId != null && !processedEventIds.add(eventId)) {
                duplicateEventCounter.increment();
                log.warn("operation=kafka_duplicate_event_detected topic={} partition={} offset={} event_id={} order_id={} correlation_id={} trace_id={}",
                        topic, partition, offset, eventId, orderId, correlationId, traceId);
                return;
            }

            if (orderId != null && !reservedOrderIds.add(orderId)) {
                idempotencyConflictCounter.increment();
                log.warn("operation=kafka_duplicate_event_detected topic={} partition={} offset={} event_id={} order_id={} correlation_id={} trace_id={}",
                        topic, partition, offset, eventId, orderId, correlationId, traceId);
                return;
            }

            if (failureSimulationProperties.poisonMessageEnabled()) {
                throw new PoisonMessageException("Simulated poison message via feature flag");
            }

            if (failureSimulationProperties.processingDelayMs() > 0) {
                Thread.sleep(failureSimulationProperties.processingDelayMs());
            }

            reservationSuccessCounter.increment();
            log.info("operation=inventory_reserved topic={} partition={} offset={} event_id={} order_id={} correlation_id={} trace_id={}",
                    topic, partition, offset, eventId, orderId, correlationId, traceId);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Interrupted while simulating processing delay", e);
        } catch (RuntimeException e) {
            log.error("operation=kafka_processing_failed topic={} partition={} offset={} event_id={} order_id={} correlation_id={} exception_type={} exception_message={}",
                    topic, partition, offset, eventId, orderId, correlationId,
                    e.getClass().getSimpleName(), e.getMessage());
            throw e;
        } finally {
            MDC.remove("correlation_id");
            MDC.remove("trace_id");
        }
    }

    private static void validatePoisonMessage(OrderCreatedEvent event) {
        BigDecimal amount = event.amount();
        if (event.orderId() == null || event.orderId().isBlank()) {
            throw new PoisonMessageException("Invalid order event: missing orderId");
        }
        if (amount == null || amount.signum() <= 0) {
            throw new PoisonMessageException("Invalid order event: amount must be greater than zero");
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
}
