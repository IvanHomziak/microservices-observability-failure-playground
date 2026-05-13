package com.playground.notificationservice.app;

import com.playground.notificationservice.domain.AckResult;
import com.playground.notificationservice.domain.DeliveryEnvelope;
import com.playground.notificationservice.domain.PubSubPort;
import org.springframework.stereotype.Component;

@Component
public class NotificationProcessor {
    private final PubSubPort pubSubPort;

    public NotificationProcessor(PubSubPort pubSubPort) {
        this.pubSubPort = pubSubPort;
    }

    public void process(DeliveryEnvelope envelope) {
        if (envelope.event() == null) {
            throw new IllegalArgumentException("Malformed payload: event body is null");
        }

        System.out.printf("[notification-service] sending %s to %s for order %s (attempt=%d, messageId=%s)%n",
                envelope.event().channel(),
                envelope.event().destination(),
                envelope.event().orderId(),
                envelope.deliveryAttempt(),
                envelope.messageId());

        AckResult ackResult = pubSubPort.ack(envelope.topic(), envelope.messageId());
        if (ackResult == AckResult.TIMEOUT) {
            throw new IllegalStateException("Ack timeout for messageId=" + envelope.messageId());
        }
    }
}
