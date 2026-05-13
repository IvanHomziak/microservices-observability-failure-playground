package com.playground.ordersservice.domain;

public enum OrderStatus {
    CREATED,
    PAYMENT_PENDING,
    PAYMENT_CONFIRMED,
    PAYMENT_FAILED,
    INVENTORY_RESERVED,
    NOTIFICATION_SENT,
    FAILED
}
