package com.playground.ordersservice.app;

import com.playground.ordersservice.api.OrderRequest;
import com.playground.ordersservice.api.OrderResponse;
import com.playground.ordersservice.domain.OrderEntity;
import com.playground.ordersservice.domain.OrderRepository;
import com.playground.ordersservice.domain.OrderStatus;
import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import com.playground.ordersservice.infra.events.NotificationPublisher;
import com.playground.ordersservice.infra.http.PaymentClient;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Service
public class OrderService {
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    private final OrderRepository repository;
    private final PaymentClient paymentClient;
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final NotificationPublisher notificationPublisher;
    private final FailureScenariosProperties failures;
    private final Counter ordersCreatedCounter;
    private final Tracer tracer;

    public OrderService(OrderRepository repository,
                        PaymentClient paymentClient,
                        KafkaTemplate<String, Object> kafkaTemplate,
                        NotificationPublisher notificationPublisher,
                        FailureScenariosProperties failures,
                        MeterRegistry meterRegistry,
                        Tracer tracer) {
        this.repository = repository;
        this.paymentClient = paymentClient;
        this.kafkaTemplate = kafkaTemplate;
        this.notificationPublisher = notificationPublisher;
        this.failures = failures;
        this.ordersCreatedCounter = meterRegistry.counter("orders.created");
        this.tracer = tracer;
    }

    public OrderResponse create(OrderRequest request) {
        String correlationId = UUID.randomUUID().toString();
        MDC.put("correlationId", correlationId);
        try {
            String orderId = UUID.randomUUID().toString();
            OrderEntity order = new OrderEntity();
            order.setOrderId(orderId);
            order.setCustomerId(request.customerId());
            order.setAmount(request.amount());
            order.setCurrency(request.currency());
            order.setCreatedAt(Instant.now());
            order.setStatus(OrderStatus.PAYMENT_PENDING);
            repository.save(order);

            log.info("event=order_created orderId={} customerId={} amount={} currency={}", orderId, request.customerId(), request.amount(), request.currency());

            boolean approved = paymentClient.authorize(orderId, order.getAmount(), order.getCurrency());
            if (!approved) {
                order.setStatus(OrderStatus.PAYMENT_FAILED);
                repository.save(order);
                log.warn("event=payment_failed orderId={}", orderId);
                return new OrderResponse(orderId, order.getStatus().name(), correlationId, currentTraceId());
            }

            order.setStatus(OrderStatus.PAYMENT_CONFIRMED);
            repository.save(order);

            if (failures.isPublishKafkaFailure()) {
                throw new IllegalStateException("Simulated kafka publish failure");
            }
            kafkaTemplate.send("order-events", Map.of("type", "OrderCreatedEvent", "orderId", orderId,
                    "customerId", request.customerId(), "amount", request.amount(), "currency", request.currency()));

            notificationPublisher.publishNotificationRequested(orderId, request.customerId());
            ordersCreatedCounter.increment();
            log.info("event=order_processed orderId={} status={}", orderId, order.getStatus().name());

            return new OrderResponse(orderId, order.getStatus().name(), correlationId, currentTraceId());
        } finally {
            MDC.remove("correlationId");
        }
    }

    private String currentTraceId() {
        return tracer.currentSpan() != null ? tracer.currentSpan().context().traceId() : "";
    }
}
