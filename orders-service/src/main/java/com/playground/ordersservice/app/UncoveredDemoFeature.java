package com.playground.ordersservice.app;

import java.math.BigDecimal;
import java.util.Objects;

/**
 * Synthetic feature used to validate the Unit Test Coverage Agent negative path.
 *
 * <p>This class is intentionally added without a matching unit test in this PR.
 * The strict coverage PR agent should reject this pull request.</p>
 */
public final class UncoveredDemoFeature {

    public boolean requiresManualReview(BigDecimal amount, String countryCode) {
        Objects.requireNonNull(amount, "amount must not be null");
        Objects.requireNonNull(countryCode, "countryCode must not be null");

        if (amount.signum() < 0) {
            throw new IllegalArgumentException("amount must not be negative");
        }

        String normalizedCountryCode = countryCode.trim().toUpperCase();
        if (normalizedCountryCode.isBlank()) {
            throw new IllegalArgumentException("countryCode must not be blank");
        }

        return amount.compareTo(new BigDecimal("750.00")) >= 0
                || "IR".equals(normalizedCountryCode)
                || "KP".equals(normalizedCountryCode);
    }
}

