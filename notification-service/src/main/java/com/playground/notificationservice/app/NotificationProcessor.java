package com.playground.notificationservice.app;

import com.playground.notificationservice.domain.AckResult;
import com.playground.notificationservice.domain.DeliveryEnvelope;
import com.playground.notificationservice.domain.PubSubPort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class NotificationProcessor {
    private static final Logger log = LoggerFactory.getLogger(NotificationProcessor.class);
    private final PubSubPort pubSubPort;
    private final String serviceName;
    private final String environment;

    public NotificationProcessor(PubSubPort pubSubPort,
                                 @Value("${spring.application.name:notification-service}") String serviceName,
                                 @Value("${app.environment:local}") String environment) {
        this.pubSubPort = pubSubPort;
        this.serviceName = serviceName;
        this.environment = environment;
    }

    public void process(DeliveryEnvelope envelope) {
        if (envelope.event() == null) {
            throw new IllegalArgumentException("Malformed payload: event body is null");
        }

        long startedAt = System.currentTimeMillis();
        log.info("event_id=pubsub-event-consumed operation=pubsub_event_consumed service={} environment={} correlation_id={} request_id={} order_id={} message_id={} topic={} channel={} destination={} delivery_attempt={}",
                serviceName, environment, envelope.correlationId(), envelope.messageId(), envelope.event().orderId(), envelope.messageId(),
                envelope.topic(), envelope.event().channel(), envelope.event().destination(), envelope.deliveryAttempt());

        AckResult ackResult = pubSubPort.ack(envelope.topic(), envelope.messageId());
        if (ackResult == AckResult.TIMEOUT) {
            log.error("event_id=pubsub-processing-failed operation=pubsub_processing_failed service={} environment={} correlation_id={} request_id={} order_id={} message_id={} exception_type={} exception_message={}",
                    serviceName, environment, envelope.correlationId(), envelope.messageId(), envelope.event().orderId(), envelope.messageId(),
                    IllegalStateException.class.getSimpleName(), "Ack timeout");
            throw new IllegalStateException("Ack timeout for messageId=" + envelope.messageId());
        }
        log.info("event_id=pubsub-event-published operation=pubsub_event_published service={} environment={} correlation_id={} request_id={} order_id={} message_id={} duration_ms={}",
                serviceName, environment, envelope.correlationId(), envelope.messageId(), envelope.event().orderId(), envelope.messageId(),
                System.currentTimeMillis() - startedAt);
    }
}
