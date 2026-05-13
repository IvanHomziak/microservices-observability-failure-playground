package com.playground.ordersservice.api.error;

import java.time.Instant;

public record ApiError(String code, String message, String correlationId, Instant timestamp) {}
