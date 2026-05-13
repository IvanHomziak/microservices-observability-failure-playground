package com.playground.apigateway.api;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(GatewayOrdersController.class)
@TestPropertySource(properties = "services.orders.base-url=http://orders-service:8081")
class GatewayOrdersControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean RestTemplate restTemplate;

    @Test
    void propagatesCorrelationIdWhenPresentAndUsesConfiguredBaseUrl() throws Exception {
        given(restTemplate.postForEntity(eq("http://orders-service:8081/orders"), any(HttpEntity.class), eq(Map.class)))
                .willReturn(ResponseEntity.ok(Map.of("status", "OK")));

        mockMvc.perform(post("/api/orders")
                        .header("X-Correlation-Id", "corr-present")
                        .contentType(APPLICATION_JSON)
                        .content("{" + "\"customerId\":\"c1\",\"amount\":10,\"currency\":\"USD\"}"))
                .andExpect(status().isOk());

        verify(restTemplate).postForEntity(eq("http://orders-service:8081/orders"), any(HttpEntity.class), eq(Map.class));
    }
}
