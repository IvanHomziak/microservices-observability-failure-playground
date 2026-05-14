package com.playground.ordersservice.infra.events;

import java.math.BigDecimal;
import java.time.Instant;

public record OrderCreatedEvent(
        String eventId,
        String orderId,
        String customerId,
        BigDecimal amount,
        String currency,
        String correlationId,
        String traceId,
        Instant createdAt
) {
}
