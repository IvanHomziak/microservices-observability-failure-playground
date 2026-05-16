package com.playground.ordersservice.app;

import com.playground.ordersservice.api.OrderRequest;
import com.playground.ordersservice.api.OrderResponse;
import com.playground.ordersservice.domain.OrderEntity;
import com.playground.ordersservice.domain.OrderRepository;
import com.playground.ordersservice.domain.OrderStatus;
import com.playground.ordersservice.infra.DatabaseOperationLatencySimulator;
import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import com.playground.ordersservice.infra.events.AuditEvent;
import com.playground.ordersservice.infra.events.AuditEventPublisher;
import com.playground.ordersservice.infra.events.NotificationPublisher;
import com.playground.ordersservice.infra.http.PaymentClient;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import com.playground.ordersservice.infra.events.OrderCreatedEvent;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.UUID;

@Service
public class OrderService {
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    private final OrderRepository repository;
    private final PaymentClient paymentClient;
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final NotificationPublisher notificationPublisher;
    private final AuditEventPublisher auditEventPublisher;
    private final FailureScenariosProperties failures;
    private final DatabaseOperationLatencySimulator dbLatencySimulator;
    private final Counter ordersCreatedCounter;
    private final Tracer tracer;
    private final boolean kafkaEventsEnabled;

    public OrderService(OrderRepository repository,
                        PaymentClient paymentClient,
                        KafkaTemplate<String, Object> kafkaTemplate,
                        NotificationPublisher notificationPublisher,
                        AuditEventPublisher auditEventPublisher,
                        FailureScenariosProperties failures,
                        DatabaseOperationLatencySimulator dbLatencySimulator,
                        MeterRegistry meterRegistry,
                        Tracer tracer,
                        @Value("${orders.events.kafka.enabled:false}") boolean kafkaEventsEnabled) {
        this.repository = repository;
        this.paymentClient = paymentClient;
        this.kafkaTemplate = kafkaTemplate;
        this.notificationPublisher = notificationPublisher;
        this.auditEventPublisher = auditEventPublisher;
        this.failures = failures;
        this.dbLatencySimulator = dbLatencySimulator;
        this.ordersCreatedCounter = meterRegistry.counter("orders.created");
        this.tracer = tracer;
        this.kafkaEventsEnabled = kafkaEventsEnabled;
    }

    public OrderResponse create(OrderRequest request, String incomingCorrelationId) {
        String correlationId = (incomingCorrelationId == null || incomingCorrelationId.isBlank())
                ? UUID.randomUUID().toString()
                : incomingCorrelationId;
        MDC.put("correlationId", correlationId);
        MDC.put("correlation_id", correlationId);
        try {
            String orderId = UUID.randomUUID().toString();
            OrderEntity order = new OrderEntity();
            order.setOrderId(orderId);
            order.setCustomerId(request.customerId());
            order.setAmount(request.amount());
            order.setCurrency(request.currency());
            order.setCreatedAt(Instant.now());
            order.setStatus(OrderStatus.PAYMENT_PENDING);
            dbLatencySimulator.simulate(orderId);
            repository.save(order);

            log.info("operation=order_persisted event_id=order_created order_id={} customer_id={} amount={} currency={}", orderId, request.customerId(), request.amount(), request.currency());
            publishAuditEvent("ORDER_CREATED", orderId, correlationId, currentTraceId());

            boolean approved = paymentClient.authorize(orderId, order.getAmount(), order.getCurrency());
            if (!approved) {
                order.setStatus(OrderStatus.PAYMENT_FAILED);
                dbLatencySimulator.simulate(orderId);
                repository.save(order);
                log.warn("operation=payment_authorization_failed event_id=payment_authorization_failed order_id={}", orderId);
                publishAuditEvent("PAYMENT_FAILED", orderId, correlationId, currentTraceId());
                return new OrderResponse(orderId, order.getStatus().name(), correlationId, currentTraceId());
            }

            publishAuditEvent("PAYMENT_CONFIRMED", orderId, correlationId, currentTraceId());

            order.setStatus(OrderStatus.PAYMENT_CONFIRMED);
            dbLatencySimulator.simulate(orderId);
            repository.save(order);

            String traceId = currentTraceId();
            String traceparent = currentTraceparent();
            if (kafkaEventsEnabled) {
                if (failures.isPublishKafkaFailure()) {
                    throw new IllegalStateException("Simulated kafka publish failure");
                }
                String eventId = UUID.randomUUID().toString();
                OrderCreatedEvent eventPayload = new OrderCreatedEvent(
                        eventId,
                        orderId,
                        request.customerId(),
                        request.amount(),
                        request.currency(),
                        correlationId,
                        traceId,
                        Instant.now()
                );
                kafkaTemplate.send(MessageBuilder.withPayload(eventPayload)
                        .setHeader(KafkaHeaders.TOPIC, "order-created")
                        .setHeader(KafkaHeaders.KEY, orderId)
                        .setHeader("correlation_id", correlationId)
                        .setHeader("traceparent", traceparent)
                        .setHeader("event_type", "OrderCreatedEvent")
                        .build());
                log.info("operation=kafka_event_published topic=order-created event_id={} order_id={} correlation_id={} trace_id={}",
                        eventId, orderId, correlationId, traceId);
            } else {
                log.info("operation=kafka_publish_skipped reason=kafka_disabled order_id={}", orderId);
            }

            notificationPublisher.publishNotificationRequested(orderId, request.customerId(), correlationId, traceId, traceparent);
            ordersCreatedCounter.increment();
            log.info("operation=order_processed event_id=order_processed order_id={} status={}", orderId, order.getStatus().name());

            return new OrderResponse(orderId, order.getStatus().name(), correlationId, currentTraceId());
        } finally {
            MDC.remove("correlationId");
            MDC.remove("correlation_id");
        }
    }

    private void publishAuditEvent(String eventType, String orderId, String correlationId, String traceId) {
        auditEventPublisher.publish(new AuditEvent(
                UUID.randomUUID().toString(),
                eventType,
                orderId,
                "orders-service",
                correlationId,
                traceId,
                Instant.now()
        ));
    }

    private String currentTraceId() {
        return tracer.currentSpan() != null ? tracer.currentSpan().context().traceId() : "";
    }

    private String currentTraceparent() {
        if (tracer.currentSpan() == null) {
            return "";
        }
        String traceId = tracer.currentSpan().context().traceId();
        String spanId = tracer.currentSpan().context().spanId();
        return "00-" + traceId + "-" + spanId + "-01";
    }
}
