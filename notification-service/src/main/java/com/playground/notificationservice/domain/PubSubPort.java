package com.playground.notificationservice.domain;

import java.util.function.Consumer;

public interface PubSubPort {
    void subscribe(String topic, Consumer<DeliveryEnvelope> handler);

    String publish(String topic, NotificationRequestedEvent event);

    AckResult ack(String topic, String messageId);
}
