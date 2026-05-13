package com.playground.inventoryservice.api;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class InventoryEventHandler {
    private final KafkaTemplate<String, Object> kafkaTemplate;
    public InventoryEventHandler(KafkaTemplate<String, Object> kafkaTemplate) { this.kafkaTemplate = kafkaTemplate; }

    @KafkaListener(topics = "order-events", groupId = "inventory-service")
    public void onOrderEvent(Map<String, Object> event) {
        kafkaTemplate.send("notification-events", Map.of("type", "INVENTORY_RESERVED", "orderId", event.get("orderId"), "customerId", event.get("customerId")));
    }
}
