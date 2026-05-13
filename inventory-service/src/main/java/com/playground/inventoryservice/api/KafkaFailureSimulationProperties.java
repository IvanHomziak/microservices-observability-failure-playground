package com.playground.inventoryservice.api;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "failure-simulation.kafka")
public record KafkaFailureSimulationProperties(
        boolean poisonMessageEnabled,
        long processingDelayMs
) {
}
