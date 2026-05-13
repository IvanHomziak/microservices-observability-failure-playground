package com.playground.ordersservice.api;

import com.playground.ordersservice.app.OrderService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService service;

    public OrderController(OrderService service) {
        this.service = service;
    }

    @PostMapping
    public OrderResponse create(@Valid @RequestBody OrderRequest request,
                                @RequestHeader(value = "X-Correlation-Id", required = false) String correlationId) {
        return service.create(request, correlationId);
    }
}
