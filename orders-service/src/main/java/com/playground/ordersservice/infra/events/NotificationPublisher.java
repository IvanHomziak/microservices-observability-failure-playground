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

    private final RestTemplate restTemplate;
    private final boolean notificationEnabled;
    private final boolean publishFailureEnabled;
    private final String notificationEventsUrl;

    public NotificationPublisher(FailureScenariosProperties failures,
                                 RestTemplate restTemplate,
                                 @Value("${orders.notifications.enabled:${orders.events.notification.enabled:false}}") boolean notificationEnabled,
                                 @Value("${orders.notifications.publish-failure-enabled:${orders.failures.publish-notification-failure:false}}") boolean publishFailureEnabled,
                                 @Value("${orders.events.notification.url}") String notificationEventsUrl) {
        this.restTemplate = restTemplate;
        this.notificationEnabled = notificationEnabled;
        this.publishFailureEnabled = publishFailureEnabled || failures.isPublishNotificationFailure();
        this.notificationEventsUrl = notificationEventsUrl;
    }

    public void publishNotificationRequested(String orderId, String customerId, String correlationId, String traceId, String traceparent) {
        if (!notificationEnabled) {
            log.info("operation=notification_publish_requested order_id={} correlation_id={} trace_id={} enabled=false", orderId, correlationId, traceId);
            return;
        }
        log.info("operation=notification_publish_requested order_id={} customer_id={} correlation_id={} trace_id={} enabled=true", orderId, customerId, correlationId, traceId);

        String eventId = UUID.randomUUID().toString();

        if (publishFailureEnabled) {
            NotificationPublishException simulatedFailure = new NotificationPublishException("Simulated notification publish failure");
            log.error("operation=notification_publish_failed event_id={} order_id={} correlation_id={} trace_id={} exception_type={} exception_message={}",
                    eventId, orderId, correlationId, traceId, simulatedFailure.getClass().getSimpleName(), simulatedFailure.getMessage());
            throw simulatedFailure;
        }

        Map<String, Object> payload = Map.of(
                "eventId", eventId,
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
            log.info("operation=notification_publish_succeeded event_id={} order_id={} customer_id={} correlation_id={} trace_id={}", eventId, orderId, customerId, correlationId, traceId);
        } catch (Exception ex) {
            log.error("operation=notification_publish_failed event_id={} order_id={} correlation_id={} trace_id={} exception_type={} exception_message={}",
                    eventId, orderId, correlationId, traceId, ex.getClass().getSimpleName(), ex.getMessage());
            throw new NotificationPublishException("Notification publish request failed", ex);
        }
    }
}
