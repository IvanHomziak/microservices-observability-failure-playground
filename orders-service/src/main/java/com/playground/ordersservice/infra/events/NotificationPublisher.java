package com.playground.ordersservice.infra.events;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class NotificationPublisher {
    private static final Logger log = LoggerFactory.getLogger(NotificationPublisher.class);
    private final FailureScenariosProperties failures;

    public NotificationPublisher(FailureScenariosProperties failures) {
        this.failures = failures;
    }

    public void publishNotificationRequested(String orderId, String customerId) {
        if (failures.isPublishNotificationFailure()) {
            throw new IllegalStateException("Simulated notification publish failure");
        }
        log.info("operation=pubsub_event_published event_id=notification_requested topic=notification-topic order_id={} payload={}",
                orderId, Map.of("type", "NotificationRequestedEvent", "orderId", orderId, "customerId", customerId));
    }
}
