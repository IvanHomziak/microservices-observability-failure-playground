package com.playground.inventoryservice.api;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "inventory.failure-simulation")
public record KafkaFailureSimulationProperties(
        boolean poisonMessageEnabled,
        boolean consumerLagModeEnabled,
        long processingDelayMs
) {
}
