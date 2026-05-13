package com.playground.ordersservice.infra.http;

public record PaymentAuthorizationResponse(
        String paymentId,
        String orderId,
        String status
) {}
