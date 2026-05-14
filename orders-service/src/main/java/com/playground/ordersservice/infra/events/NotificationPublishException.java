package com.playground.ordersservice.infra.events;

public class NotificationPublishException extends RuntimeException {
    public NotificationPublishException(String message, Throwable cause) {
        super(message, cause);
    }

    public NotificationPublishException(String message) {
        super(message);
    }
}
