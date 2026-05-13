package com.playground.inventoryservice.api;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class InventoryEventHandlerTest {

    @Test
    void shouldRejectPoisonMessageScenario() {
        InventoryEventHandler handler = new InventoryEventHandler(
                new SimpleMeterRegistry(),
                new KafkaFailureSimulationProperties(false, 0)
        );

        Map<String, Object> event = new HashMap<>();
        event.put("eventId", "e1");
        event.put("orderId", "o1");
        event.put("failureScenario", "poison-message");

        assertThatThrownBy(() -> handler.onOrderCreated(event, "order-events", 0, 1L, null, "corr-1", null))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Simulated poison message");
    }

    @Test
    void shouldHandleDuplicateEventWithoutThrowing() {
        InventoryEventHandler handler = new InventoryEventHandler(
                new SimpleMeterRegistry(),
                new KafkaFailureSimulationProperties(false, 0)
        );

        Map<String, Object> event = new HashMap<>();
        event.put("eventId", "duplicate-event");
        event.put("orderId", "order-1");

        handler.onOrderCreated(event, "order-events", 0, 1L, null, "corr-1", null);
        handler.onOrderCreated(event, "order-events", 0, 2L, null, "corr-1", null);
    }
}
