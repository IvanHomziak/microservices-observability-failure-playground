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

        log.info("operation=pubsub_event_consumed event_id=notification_requested order_id={} channel={} destination={} delivery_attempt={} message_id={}",
                envelope.event().orderId(), envelope.event().channel(), envelope.event().destination(), envelope.deliveryAttempt(), envelope.messageId());

        AckResult ackResult = pubSubPort.ack(envelope.topic(), envelope.messageId());
        if (ackResult == AckResult.TIMEOUT) {
            log.error("operation=pubsub_processing_failed event_id=notification_ack_timeout order_id={} exception_type=IllegalStateException exception_message={}",
                    envelope.event().orderId(), "Ack timeout for messageId=" + envelope.messageId());
            throw new IllegalStateException("Ack timeout for messageId=" + envelope.messageId());
        }
    }
}
