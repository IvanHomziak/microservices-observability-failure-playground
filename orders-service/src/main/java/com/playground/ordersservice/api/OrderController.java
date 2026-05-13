package com.playground.ordersservice.api;

import com.playground.ordersservice.app.OrderService;
import com.playground.ordersservice.domain.OrderEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService service;
    public OrderController(OrderService service) { this.service = service; }

    @PostMapping
    public OrderEntity create(@RequestBody OrderRequest request) { return service.create(request); }
}
