package com.playground.inventoryservice.api;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class InventoryEventHandlerTest {

    @Test
    void shouldRejectPoisonMessageScenario() {
        InventoryEventHandler handler = new InventoryEventHandler(
                new SimpleMeterRegistry(),
                new KafkaFailureSimulationProperties(true, false, 0)
        );

        OrderCreatedEvent event = new OrderCreatedEvent("e1", "o1", "c1", BigDecimal.TEN, "USD", "corr-1", "trace-1", Instant.now());

        assertThatThrownBy(() -> handler.onOrderCreated(event, "order-created", 0, 1L, "corr-1", null))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Simulated poison message");
    }

    @Test
    void shouldHandleDuplicateEventWithoutThrowing() {
        InventoryEventHandler handler = new InventoryEventHandler(
                new SimpleMeterRegistry(),
                new KafkaFailureSimulationProperties(false, false, 0)
        );

        OrderCreatedEvent event = new OrderCreatedEvent("duplicate-event", "order-1", "c1", BigDecimal.ONE, "USD", "corr-1", "trace-1", Instant.now());

        handler.onOrderCreated(event, "order-created", 0, 1L, "corr-1", null);
        handler.onOrderCreated(event, "order-created", 0, 2L, "corr-1", null);
    }
}
