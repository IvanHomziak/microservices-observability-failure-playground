package com.playground.notificationservice.infra;

import com.playground.notificationservice.app.FailureConfig;
import com.playground.notificationservice.app.FailureMode;
import com.playground.notificationservice.domain.AckResult;
import com.playground.notificationservice.domain.DeliveryEnvelope;
import com.playground.notificationservice.domain.NotificationRequestedEvent;
import com.playground.notificationservice.domain.PubSubPort;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;

@Component
public class InMemoryPubSubAdapter implements PubSubPort {
    private static final String VALID_TOPIC = "notification-events";

    private final FailureConfig failureConfig;
    private final Map<String, Consumer<DeliveryEnvelope>> subscribers = new ConcurrentHashMap<>();

    public InMemoryPubSubAdapter(FailureConfig failureConfig) {
        this.failureConfig = failureConfig;
    }

    @Override
    public void subscribe(String topic, Consumer<DeliveryEnvelope> handler) {
        subscribers.put(topic, handler);
    }

    @Override
    public String publish(String topic, NotificationRequestedEvent event) {
        FailureMode mode = failureConfig.getMode();

        if (mode == FailureMode.INVALID_TOPIC || !VALID_TOPIC.equals(topic)) {
            throw new IllegalArgumentException("Invalid topic: " + topic);
        }
        if (mode == FailureMode.PUBLISH_FAILURE) {
            throw new IllegalStateException("Simulated publish failure");
        }

        NotificationRequestedEvent payload = (mode == FailureMode.MALFORMED_PAYLOAD) ? null : event;
        String messageId = UUID.randomUUID().toString();
        Consumer<DeliveryEnvelope> consumer = subscribers.get(topic);
        if (consumer == null) {
            throw new IllegalStateException("No subscriber for topic: " + topic);
        }

        int attempts = mode == FailureMode.DUPLICATE_DELIVERY ? 2 : 1;
        for (int attempt = 1; attempt <= attempts; attempt++) {
            if (mode == FailureMode.PROCESSING_DELAY) {
                sleep(2_000);
            }
            consumer.accept(new DeliveryEnvelope(messageId, topic, payload, attempt));
        }

        return messageId;
    }

    @Override
    public AckResult ack(String topic, String messageId) {
        if (failureConfig.getMode() == FailureMode.ACK_TIMEOUT) {
            sleep(1_000);
            return AckResult.TIMEOUT;
        }
        return AckResult.ACKED;
    }

    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
