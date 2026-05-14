package com.playground.inventoryservice.api;

public class PoisonMessageException extends RuntimeException {
    public PoisonMessageException(String message) {
        super(message);
    }
}
