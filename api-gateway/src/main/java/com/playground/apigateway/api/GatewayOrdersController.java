package com.playground.apigateway.api;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;

@RestController
@RequestMapping("/api/orders")
public class GatewayOrdersController {
    private final RestTemplate restTemplate;
    private final String ordersServiceUrl;

    public GatewayOrdersController(
            RestTemplate restTemplate,
            @Value("${services.orders.base-url:http://localhost:8081}") String ordersServiceUrl
    ) {
        this.restTemplate = restTemplate;
        this.ordersServiceUrl = ordersServiceUrl;
    }

    @PostMapping
    public ResponseEntity<Map> create(@RequestBody Map<String, Object> request, HttpServletRequest servletRequest) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        String correlationId = servletRequest.getHeader("X-Correlation-Id");
        if (correlationId != null && !correlationId.isBlank()) {
            headers.set("X-Correlation-Id", correlationId);
        }

        HttpEntity<Map<String, Object>> payload = new HttpEntity<>(request, headers);
        return restTemplate.postForEntity(ordersServiceUrl + "/orders", payload, Map.class);
    }
}
