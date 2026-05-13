package com.playground.paymentsservice.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "failure-simulation.payments")
public record PaymentFailureSimulationProperties(
        long delayMs,
        int forcedStatusCode,
        double failureRate,
        boolean invalidJsonEnabled,
        boolean declineEnabled,
        boolean timeoutEnabled
) {
}
