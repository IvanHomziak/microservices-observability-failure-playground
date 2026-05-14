package com.playground.apigateway.api;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/orders")
public class GatewayOrdersController {
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String ordersServiceUrl;

    public GatewayOrdersController(
            RestTemplate restTemplate,
            ObjectMapper objectMapper,
            @Value("${services.orders.base-url}") String ordersServiceUrl
    ) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
        this.ordersServiceUrl = ordersServiceUrl;
    }

    @PostMapping
    public ResponseEntity<Object> create(@RequestBody Map<String, Object> request, HttpServletRequest servletRequest) {
        String correlationId = resolveCorrelationId(servletRequest);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (correlationId != null && !correlationId.isBlank()) {
            headers.set("X-Correlation-Id", correlationId);
        }

        HttpEntity<Map<String, Object>> payload = new HttpEntity<>(request, headers);
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(ordersServiceUrl + "/orders", payload, Map.class);
            return ResponseEntity.status(response.getStatusCode())
                    .headers(withCorrelation(response.getHeaders(), correlationId))
                    .body(response.getBody());
        } catch (HttpStatusCodeException ex) {
            return ResponseEntity.status(ex.getStatusCode())
                    .headers(withCorrelation(new HttpHeaders(), correlationId))
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(safeDownstreamErrorBody(ex, correlationId));
        }
    }

    private String resolveCorrelationId(HttpServletRequest servletRequest) {
        String correlationId = servletRequest.getHeader("X-Correlation-Id");
        if (correlationId == null || correlationId.isBlank()) {
            Object requestAttribute = servletRequest.getAttribute("X-Correlation-Id");
            if (requestAttribute instanceof String value && !value.isBlank()) {
                return value;
            }
        }
        return correlationId;
    }

    private HttpHeaders withCorrelation(HttpHeaders source, String correlationId) {
        HttpHeaders headers = new HttpHeaders();
        headers.putAll(source);
        if (correlationId != null && !correlationId.isBlank()) {
            headers.set("X-Correlation-Id", correlationId);
        }
        return headers;
    }

    private Object safeDownstreamErrorBody(HttpStatusCodeException ex, String correlationId) {
        String rawBody = ex.getResponseBodyAsString();
        if (rawBody != null && !rawBody.isBlank()) {
            try {
                return objectMapper.readValue(rawBody, new TypeReference<Map<String, Object>>() {});
            } catch (Exception ignored) {
                // intentionally fall back to controlled gateway error below
            }
        }

        Map<String, Object> fallback = new LinkedHashMap<>();
        fallback.put("code", "DOWNSTREAM_ERROR");
        fallback.put("message", "Downstream service returned an error");
        fallback.put("correlationId", correlationId);
        fallback.put("timestamp", Instant.now().toString());
        return fallback;
    }
}
