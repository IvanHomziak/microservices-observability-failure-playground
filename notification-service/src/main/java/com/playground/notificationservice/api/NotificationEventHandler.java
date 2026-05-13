package com.playground.notificationservice.api;

import com.playground.notificationservice.app.NotificationProcessor;
import com.playground.notificationservice.domain.PubSubPort;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;

@Component
public class NotificationEventHandler {
    private final PubSubPort pubSubPort;
    private final NotificationProcessor notificationProcessor;

    public NotificationEventHandler(PubSubPort pubSubPort, NotificationProcessor notificationProcessor) {
        this.pubSubPort = pubSubPort;
        this.notificationProcessor = notificationProcessor;
    }

    @PostConstruct
    void subscribe() {
        pubSubPort.subscribe("notification-events", notificationProcessor::process);
    }
}
