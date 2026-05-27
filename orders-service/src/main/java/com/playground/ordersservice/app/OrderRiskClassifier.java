package com.playground.ordersservice.app;

import java.math.BigDecimal;
import java.util.Locale;
import java.util.Objects;

public final class OrderRiskClassifier {

    public enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH
    }

    public RiskLevel classify(BigDecimal amount, String currency) {
        Objects.requireNonNull(amount, "amount must not be null");
        Objects.requireNonNull(currency, "currency must not be null");

        if (amount.signum() < 0) {
            throw new IllegalArgumentException("amount must not be negative");
        }

        String normalizedCurrency = currency.trim().toUpperCase(Locale.ROOT);
        if (normalizedCurrency.isBlank()) {
            throw new IllegalArgumentException("currency must not be blank");
        }

        if ("BTC".equals(normalizedCurrency)) {
            return RiskLevel.HIGH;
        }

        if (amount.compareTo(new BigDecimal("1000.00")) >= 0) {
            return RiskLevel.HIGH;
        }

        if ("USD".equals(normalizedCurrency)) {
            return RiskLevel.MEDIUM;
        }

        if (amount.compareTo(new BigDecimal("500.00")) >= 0) {
            return RiskLevel.MEDIUM;
        }

        return RiskLevel.LOW;
    }
}
