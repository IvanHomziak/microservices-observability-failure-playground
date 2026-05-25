package com.playground.ordersservice.app;

import java.math.BigDecimal;
import java.util.Objects;

/**
 * Synthetic feature used to validate the Unit Test Coverage Agent report.
 *
 * <p>This class is intentionally pure Java and has no Spring, database, Kafka,
 * or network dependencies. It gives the coverage agent a deterministic
 * production-code change that can be mapped to JaCoCo evidence.</p>
 */
public final class OrderRiskClassifier {
    private static final BigDecimal HIGH_RISK_AMOUNT = new BigDecimal("1000.00");
    private static final BigDecimal MEDIUM_RISK_AMOUNT = new BigDecimal("500.00");

    public RiskLevel classify(BigDecimal amount, String currency) {
        Objects.requireNonNull(amount, "amount must not be null");
        Objects.requireNonNull(currency, "currency must not be null");

        if (amount.signum() < 0) {
            throw new IllegalArgumentException("amount must not be negative");
        }

        String normalizedCurrency = currency.trim().toUpperCase();
        if (normalizedCurrency.isBlank()) {
            throw new IllegalArgumentException("currency must not be blank");
        }

        if (amount.compareTo(HIGH_RISK_AMOUNT) >= 0 || "BTC".equals(normalizedCurrency)) {
            return RiskLevel.HIGH;
        }

        if (amount.compareTo(MEDIUM_RISK_AMOUNT) >= 0 || "USD".equals(normalizedCurrency)) {
            return RiskLevel.MEDIUM;
        }

        return RiskLevel.LOW;
    }

    public enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH
    }
}
