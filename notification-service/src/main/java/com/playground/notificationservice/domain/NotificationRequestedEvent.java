package com.playground.notificationservice.domain;

import jakarta.validation.constraints.NotBlank;

public record NotificationRequestedEvent(
        @NotBlank String eventId,
        @NotBlank String orderId,
        @NotBlank String userId,
        @NotBlank String channel,
        @NotBlank String destination,
        @NotBlank String message
) {
}
