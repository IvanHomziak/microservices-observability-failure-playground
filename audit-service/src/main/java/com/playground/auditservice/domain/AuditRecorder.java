package com.playground.auditservice.domain;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class AuditRecorder {
    private static final Logger log = LoggerFactory.getLogger(AuditRecorder.class);

    public void record(AuditEvent event, String channel) {
        log.info(
                "operation=audit_event_received channel={} event_id={} event_type={} order_id={} source_service={} correlation_id={} trace_id={}",
                channel,
                sanitize(event.eventId()),
                sanitize(event.eventType()),
                sanitize(event.orderId()),
                sanitize(event.sourceService()),
                sanitize(event.correlationId()),
                sanitize(event.traceId())
        );
    }

    private static String sanitize(String value) {
        return value == null || value.isBlank() ? "n/a" : value;
    }
}
