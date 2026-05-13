package com.playground.notificationservice.api;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class NotificationEventHandler {
    @KafkaListener(topics = "notification-events", groupId = "notification-service")
    public void onNotificationEvent(Map<String, Object> event) {
        System.out.println("Notification sent for order " + event.get("orderId"));
    }
}
