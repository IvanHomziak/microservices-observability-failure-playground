package com.playground.auditservice.domain;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Set;

@Component
public class AuditRecorder {
    private static final Logger log = LoggerFactory.getLogger(AuditRecorder.class);

    private static final Set<String> IMPORTANT_EVENTS = Set.of(
            "ORDER_CREATED",
            "PAYMENT_AUTHORIZED",
            "PAYMENT_FAILED",
            "INVENTORY_RESERVED",
            "INVENTORY_FAILED",
            "NOTIFICATION_SENT",
            "NOTIFICATION_FAILED"
    );

    public void record(Map<String, Object> event, String source) {
        String eventType = String.valueOf(event.getOrDefault("type", "UNKNOWN"));
        if (!IMPORTANT_EVENTS.contains(eventType)) {
            return;
        }

        String orderId = String.valueOf(event.getOrDefault("orderId", "n/a"));
        String traceId = firstNonBlank(
                asString(event.get("traceId")),
                MDC.get("traceId"),
                MDC.get("trace_id"),
                "n/a"
        );
        String spanId = firstNonBlank(
                asString(event.get("spanId")),
                MDC.get("spanId"),
                MDC.get("span_id"),
                "n/a"
        );

        log.info(
                "audit_event type={} source={} orderId={} traceId={} spanId={} payload={}",
                eventType,
                source,
                orderId,
                traceId,
                spanId,
                event
        );
    }

    private static String asString(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value;
            }
        }
        return "n/a";
    }
}
