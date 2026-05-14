package com.playground.ordersservice.infra.events;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Component
public class AuditEventPublisher {
    private static final Logger log = LoggerFactory.getLogger(AuditEventPublisher.class);

    private final RestTemplate restTemplate;
    private final String auditUrl;
    private final boolean enabled;

    public AuditEventPublisher(RestTemplateBuilder restTemplateBuilder,
                               @Value("${orders.audit.url:http://localhost:8085/audit/events}") String auditUrl,
                               @Value("${orders.audit.enabled:false}") boolean enabled) {
        this.restTemplate = restTemplateBuilder
                .setConnectTimeout(Duration.ofMillis(500))
                .setReadTimeout(Duration.ofMillis(1000))
                .build();
        this.auditUrl = auditUrl;
        this.enabled = enabled;
    }

    public void publish(AuditEvent event) {
        if (!enabled) {
            return;
        }
        try {
            restTemplate.postForEntity(auditUrl, new HttpEntity<>(event), Void.class);
            log.info("operation=audit_event_published event_id={} event_type={} order_id={} correlation_id={} trace_id={}",
                    event.eventId(), event.eventType(), event.orderId(), event.correlationId(), event.traceId());
        } catch (RestClientException ex) {
            log.warn("operation=audit_event_publish_failed event_id={} event_type={} order_id={} message={}",
                    event.eventId(), event.eventType(), event.orderId(), ex.getMessage());
        }
    }
}
