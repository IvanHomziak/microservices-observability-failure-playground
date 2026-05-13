package com.playground.ordersservice.app;

import com.playground.ordersservice.api.OrderRequest;
import com.playground.ordersservice.domain.*;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Service
public class OrderService {
    private final OrderRepository repository;
    private final RestTemplate restTemplate;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public OrderService(OrderRepository repository, RestTemplate restTemplate, KafkaTemplate<String, Object> kafkaTemplate) {
        this.repository = repository;
        this.restTemplate = restTemplate;
        this.kafkaTemplate = kafkaTemplate;
    }

    public OrderEntity create(OrderRequest request) {
        OrderEntity order = new OrderEntity();
        order.setOrderId(UUID.randomUUID().toString());
        order.setCustomerId(request.customerId());
        order.setAmount(request.amount());
        order.setCurrency(request.currency());
        order.setCreatedAt(Instant.now());
        order.setStatus(OrderStatus.CREATED);
        repository.save(order);

        order.setStatus(OrderStatus.PAYMENT_PENDING);
        repository.save(order);

        var payment = restTemplate.postForObject("http://localhost:8082/payments/authorize", Map.of(
                "orderId", order.getOrderId(), "amount", order.getAmount(), "currency", order.getCurrency()), Map.class);

        boolean approved = payment != null && Boolean.TRUE.equals(payment.get("approved"));
        if (!approved) {
            order.setStatus(OrderStatus.PAYMENT_FAILED);
            repository.save(order);
            return order;
        }

        order.setStatus(OrderStatus.PAYMENT_CONFIRMED);
        repository.save(order);

        kafkaTemplate.send("order-events", Map.of("type", "PAYMENT_CONFIRMED", "orderId", order.getOrderId(), "customerId", order.getCustomerId()));
        return order;
    }
}
