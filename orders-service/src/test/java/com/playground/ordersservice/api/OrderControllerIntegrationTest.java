package com.playground.ordersservice.api;

import com.playground.ordersservice.domain.OrderEntity;
import com.playground.ordersservice.domain.OrderRepository;
import com.playground.ordersservice.infra.events.NotificationPublisher;
import com.playground.ordersservice.infra.http.PaymentClient;
import io.micrometer.tracing.Tracer;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class OrderControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderRepository orderRepository;
    @MockBean
    private PaymentClient paymentClient;
    @MockBean
    private KafkaTemplate<String, Object> kafkaTemplate;
    @MockBean
    private NotificationPublisher notificationPublisher;
    @MockBean
    private Tracer tracer;

    @Test
    void shouldCreateOrderSuccessfully() throws Exception {
        when(paymentClient.authorize(anyString(), any(BigDecimal.class), anyString())).thenReturn(true);
        when(orderRepository.save(any(OrderEntity.class))).thenAnswer(invocation -> invocation.getArgument(0));

        mockMvc.perform(post("/orders")
                        .contentType("application/json")
                        .header("X-Correlation-Id", "corr-success")
                        .content("""
                                {"customerId":"c1","amount":10.50,"currency":"USD"}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("PAYMENT_CONFIRMED"))
                .andExpect(jsonPath("$.correlationId").value("corr-success"));
    }

    @Test
    void shouldReturnErrorWithCorrelationIdWhenPaymentTimesOut() throws Exception {
        when(paymentClient.authorize(anyString(), any(BigDecimal.class), anyString()))
                .thenThrow(new com.playground.ordersservice.infra.http.PaymentGatewayException("PAYMENT_TIMEOUT", "Timeout while calling payment service"));
        when(orderRepository.save(any(OrderEntity.class))).thenAnswer(invocation -> invocation.getArgument(0));

        mockMvc.perform(post("/orders")
                        .contentType("application/json")
                        .header("X-Correlation-Id", "corr-timeout")
                        .content("""
                                {"customerId":"c2","amount":12.00,"currency":"USD"}
                                """))
                .andExpect(status().isGatewayTimeout())
                .andExpect(jsonPath("$.code").value("PAYMENT_TIMEOUT"))
                .andExpect(jsonPath("$.correlationId").value("corr-timeout"));
    }
}
