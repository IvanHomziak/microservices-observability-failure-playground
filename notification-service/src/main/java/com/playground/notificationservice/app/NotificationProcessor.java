package com.playground.notificationservice.app;

import com.playground.notificationservice.domain.AckResult;
import com.playground.notificationservice.domain.DeliveryEnvelope;
import com.playground.notificationservice.domain.PubSubPort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class NotificationProcessor {
    private static final Logger log = LoggerFactory.getLogger(NotificationProcessor.class);
    private final PubSubPort pubSubPort;

    public NotificationProcessor(PubSubPort pubSubPort) {
        this.pubSubPort = pubSubPort;
    }

    public void process(DeliveryEnvelope envelope) {
        if (envelope.event() == null) {
            throw new IllegalArgumentException("Malformed payload: event body is null");
        }

        log.info("operation=notification_event_received event_id={} order_id={} customer_id={} correlation_id={} trace_id={} message_id={} delivery_attempt={}",
                envelope.event().eventId(), envelope.event().orderId(), envelope.event().customerId(), envelope.event().correlationId(), envelope.event().traceId(), envelope.messageId(), envelope.deliveryAttempt());

        try {
            AckResult ackResult = pubSubPort.ack(envelope.topic(), envelope.messageId());
            if (ackResult == AckResult.TIMEOUT) {
                log.error("operation=notification_failed event_id={} order_id={} customer_id={} correlation_id={} trace_id={} reason=ack_timeout",
                        envelope.event().eventId(), envelope.event().orderId(), envelope.event().customerId(), envelope.event().correlationId(), envelope.event().traceId());
                throw new IllegalStateException("Ack timeout for messageId=" + envelope.messageId());
            }
            log.info("operation=notification_sent event_id={} order_id={} customer_id={} correlation_id={} trace_id={} channel={}",
                    envelope.event().eventId(), envelope.event().orderId(), envelope.event().customerId(), envelope.event().correlationId(), envelope.event().traceId(), envelope.event().channel());
        } catch (Exception ex) {
            log.error("operation=notification_failed event_id={} order_id={} customer_id={} correlation_id={} trace_id={} exception_type={} exception_message={}",
                    envelope.event().eventId(), envelope.event().orderId(), envelope.event().customerId(), envelope.event().correlationId(), envelope.event().traceId(), ex.getClass().getSimpleName(), ex.getMessage());
            throw ex;
        }
    }
}
