package com.playground.ordersservice.infra.events;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Component
public class NotificationPublisher {
    private static final Logger log = LoggerFactory.getLogger(NotificationPublisher.class);

    private final FailureScenariosProperties failures;
    private final RestTemplate restTemplate;
    private final boolean notificationEnabled;
    private final String notificationEventsUrl;

    public NotificationPublisher(FailureScenariosProperties failures,
                                 RestTemplate restTemplate,
                                 @Value("${orders.events.notification.enabled:false}") boolean notificationEnabled,
                                 @Value("${orders.events.notification.url:http://localhost:8084/api/notifications/events}") String notificationEventsUrl) {
        this.failures = failures;
        this.restTemplate = restTemplate;
        this.notificationEnabled = notificationEnabled;
        this.notificationEventsUrl = notificationEventsUrl;
    }

    public void publishNotificationRequested(String orderId, String customerId, String correlationId, String traceId, String traceparent) {
        if (!notificationEnabled) {
            log.info("operation=notification_publish_requested order_id={} correlation_id={} trace_id={} enabled=false", orderId, correlationId, traceId);
            return;
        }
        log.info("operation=notification_publish_requested order_id={} customer_id={} correlation_id={} trace_id={} enabled=true", orderId, customerId, correlationId, traceId);

        if (failures.isPublishNotificationFailure()) {
            log.error("operation=notification_publish_failed order_id={} correlation_id={} trace_id={} reason=simulated_failure", orderId, correlationId, traceId);
            throw new IllegalStateException("Simulated notification publish failure");
        }

        Map<String, Object> payload = Map.of(
                "eventId", UUID.randomUUID().toString(),
                "orderId", orderId,
                "customerId", customerId,
                "channel", "EMAIL",
                "correlationId", correlationId,
                "traceId", traceId,
                "createdAt", Instant.now().toString()
        );

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("traceparent", traceparent);
            headers.set("X-Correlation-Id", correlationId);
            restTemplate.postForEntity(notificationEventsUrl, new HttpEntity<>(payload, headers), String.class);
            log.info("operation=notification_publish_succeeded order_id={} customer_id={} correlation_id={} trace_id={}", orderId, customerId, correlationId, traceId);
        } catch (Exception ex) {
            log.error("operation=notification_publish_failed order_id={} customer_id={} correlation_id={} trace_id={} exception_type={} exception_message={}",
                    orderId, customerId, correlationId, traceId, ex.getClass().getSimpleName(), ex.getMessage());
            throw ex;
        }
    }
}
