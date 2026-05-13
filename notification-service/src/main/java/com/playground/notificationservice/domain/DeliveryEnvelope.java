package com.playground.notificationservice.domain;

public record DeliveryEnvelope(
        String messageId,
        String topic,
        NotificationRequestedEvent event,
        int deliveryAttempt
) {
}
