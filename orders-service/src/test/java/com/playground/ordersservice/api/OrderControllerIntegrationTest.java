package com.playground.ordersservice.api;

import com.playground.ordersservice.app.OrderService;
import com.playground.ordersservice.infra.http.PaymentGatewayException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
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

    private static final String SUCCESS_CORRELATION_ID = "corr-success";
    private static final String PAYMENT_TIMEOUT_CORRELATION_ID = "corr-timeout";

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @BeforeEach
    void clearMdcBeforeTest() {
        MDC.clear();
    }

    @AfterEach
    void clearMdcAfterTest() {
        MDC.clear();
    }

    @Test
    void shouldCreateOrderSuccessfully() throws Exception {
        when(orderService.create(any(OrderRequest.class), eq(SUCCESS_CORRELATION_ID)))
                .thenReturn(new OrderResponse("order-1", "PAYMENT_CONFIRMED", SUCCESS_CORRELATION_ID, "trace-1"));

        mockMvc.perform(post("/orders")
                        .contentType("application/json")
                        .header("X-Correlation-Id", SUCCESS_CORRELATION_ID)
                        .content("""
                                {"customerId":"c1","amount":10.50,"currency":"USD"}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("PAYMENT_CONFIRMED"))
                .andExpect(jsonPath("$.correlationId").value(SUCCESS_CORRELATION_ID));
    }

    @Test
    void shouldReturnErrorWithCorrelationIdWhenPaymentTimesOut() throws Exception {
        MDC.put("correlationId", PAYMENT_TIMEOUT_CORRELATION_ID);
        MDC.put("correlation_id", PAYMENT_TIMEOUT_CORRELATION_ID);

        when(orderService.create(any(OrderRequest.class), eq(PAYMENT_TIMEOUT_CORRELATION_ID)))
                .thenThrow(new PaymentGatewayException("PAYMENT_TIMEOUT", "Timeout while calling payment service"));

        mockMvc.perform(post("/orders")
                        .contentType("application/json")
                        .header("X-Correlation-Id", PAYMENT_TIMEOUT_CORRELATION_ID)
                        .content("""
                                {"customerId":"c2","amount":12.00,"currency":"USD"}
                                """))
                .andExpect(status().isGatewayTimeout())
                .andExpect(jsonPath("$.code").value("PAYMENT_TIMEOUT"))
                .andExpect(jsonPath("$.correlationId").value(PAYMENT_TIMEOUT_CORRELATION_ID));
    }
}
