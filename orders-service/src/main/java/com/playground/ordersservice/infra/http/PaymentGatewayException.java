package com.playground.ordersservice.infra.http;

public class PaymentGatewayException extends RuntimeException {
    private final String code;

    public PaymentGatewayException(String code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
    }

    public PaymentGatewayException(String code, String message) {
        super(message);
        this.code = code;
    }

    public String getCode() {
        return code;
    }
}
