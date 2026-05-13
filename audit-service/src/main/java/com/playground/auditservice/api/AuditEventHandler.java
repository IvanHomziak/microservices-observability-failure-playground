package com.playground.auditservice.api;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class AuditEventHandler {
    @KafkaListener(topics = {"order-events", "notification-events"}, groupId = "audit-service")
    public void onAnyEvent(Map<String, Object> event) {
        System.out.println("AUDIT EVENT: " + event);
    }
}
