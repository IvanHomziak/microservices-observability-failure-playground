package com.playground.paymentsservice.app.dto;

public record PaymentAuthorizationResponse(
        String paymentId,
        String orderId,
        String status
) {
}
