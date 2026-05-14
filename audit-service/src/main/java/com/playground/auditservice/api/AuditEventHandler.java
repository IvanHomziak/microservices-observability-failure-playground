package com.playground.auditservice.api;

import com.playground.auditservice.domain.AuditEvent;
import com.playground.auditservice.domain.AuditRecorder;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix = "audit.kafka", name = "enabled", havingValue = "true")
public class AuditEventHandler {
    private final AuditRecorder auditRecorder;

    public AuditEventHandler(AuditRecorder auditRecorder) {
        this.auditRecorder = auditRecorder;
    }

    @KafkaListener(topics = "audit-events", groupId = "audit-service")
    public void onAuditEvent(AuditEvent event) {
        auditRecorder.record(event, "kafka");
    }
}
