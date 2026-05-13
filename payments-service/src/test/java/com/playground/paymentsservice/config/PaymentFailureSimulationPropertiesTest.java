package com.playground.paymentsservice.config;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class PaymentFailureSimulationPropertiesTest {
    @Test
    void shouldExposeConfiguredValues() {
        PaymentFailureSimulationProperties properties = new PaymentFailureSimulationProperties(250L, 503, 0.25, true, false, true);

        assertThat(properties.delayMs()).isEqualTo(250L);
        assertThat(properties.forcedStatusCode()).isEqualTo(503);
        assertThat(properties.failureRate()).isEqualTo(0.25);
        assertThat(properties.invalidJsonEnabled()).isTrue();
        assertThat(properties.declineEnabled()).isFalse();
        assertThat(properties.timeoutEnabled()).isTrue();
    }
}
