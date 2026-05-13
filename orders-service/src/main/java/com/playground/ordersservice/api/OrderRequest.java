package com.playground.ordersservice.api;

import java.math.BigDecimal;

public record OrderRequest(String customerId, BigDecimal amount, String currency) {}
