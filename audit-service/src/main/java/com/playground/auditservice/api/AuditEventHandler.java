package com.playground.auditservice.api;

import com.playground.auditservice.domain.AuditRecorder;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class AuditEventHandler {
    private final AuditRecorder auditRecorder;

    public AuditEventHandler(AuditRecorder auditRecorder) {
        this.auditRecorder = auditRecorder;
    }

    @KafkaListener(topics = {"order-events", "payment-events", "inventory-events", "notification-events"}, groupId = "audit-service")
    public void onAnyEvent(Map<String, Object> event) {
        auditRecorder.record(event, "kafka");
    }
}
