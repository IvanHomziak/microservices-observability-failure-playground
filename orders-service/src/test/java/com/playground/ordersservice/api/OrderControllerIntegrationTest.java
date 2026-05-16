package com.playground.ordersservice.api;

import com.playground.ordersservice.app.OrderService;
import com.playground.ordersservice.infra.http.PaymentGatewayException;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;


import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(OrderController.class)
class OrderControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Test
    void shouldCreateOrderSuccessfully() throws Exception {
        when(orderService.create(any(OrderRequest.class), eq("corr-success")))
                .thenReturn(new OrderResponse("order-1", "PAYMENT_CONFIRMED", "corr-success", "trace-1"));

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
        when(orderService.create(any(OrderRequest.class), eq("corr-timeout")))
                .thenThrow(new PaymentGatewayException("PAYMENT_TIMEOUT", "Timeout while calling payment service"));

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
