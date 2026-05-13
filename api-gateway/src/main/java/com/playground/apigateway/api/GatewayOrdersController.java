package com.playground.apigateway.api;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/api/orders")
public class GatewayOrdersController {
    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping
    public Map<String, Object> create(@RequestBody Map<String, Object> request) {
        return restTemplate.postForObject("http://localhost:8081/orders", request, Map.class);
    }
}
