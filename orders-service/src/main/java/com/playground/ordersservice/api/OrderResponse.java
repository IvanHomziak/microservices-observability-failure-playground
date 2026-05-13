package com.playground.ordersservice.api;

public record OrderResponse(
        String orderId,
        String status,
        String correlationId,
        String traceId
) {}
