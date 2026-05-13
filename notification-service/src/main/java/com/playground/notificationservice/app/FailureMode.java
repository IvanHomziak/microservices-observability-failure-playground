package com.playground.notificationservice.app;

public enum FailureMode {
    NONE,
    INVALID_TOPIC,
    PUBLISH_FAILURE,
    ACK_TIMEOUT,
    DUPLICATE_DELIVERY,
    PROCESSING_DELAY,
    MALFORMED_PAYLOAD
}
