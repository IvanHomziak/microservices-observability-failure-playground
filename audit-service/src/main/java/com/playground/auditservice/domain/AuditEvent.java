package com.playground.auditservice.domain;

import java.time.Instant;

public record AuditEvent(
        String eventId,
        String eventType,
        String orderId,
        String sourceService,
        String correlationId,
        String traceId,
        Instant createdAt
) {
}
