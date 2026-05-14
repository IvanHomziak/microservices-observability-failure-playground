package com.playground.notificationservice.domain;

import jakarta.validation.constraints.NotBlank;

public record NotificationRequestedEvent(
        @NotBlank String eventId,
        @NotBlank String orderId,
        @NotBlank String customerId,
        @NotBlank String channel,
        @NotBlank String correlationId,
        @NotBlank String traceId,
        @NotBlank String createdAt
) {
}
