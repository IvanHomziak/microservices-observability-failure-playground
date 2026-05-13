package com.playground.ordersservice.api.error;

import com.playground.ordersservice.api.OrderController;
import com.playground.ordersservice.app.OrderService;
import com.playground.ordersservice.infra.http.PaymentGatewayException;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(OrderController.class)
@Import(GlobalExceptionHandler.class)
class GlobalExceptionHandlerTest {
    @Autowired MockMvc mockMvc;
    @MockBean OrderService orderService;

    @Test
    void paymentTimeoutMapsToHttp504AndContainsCorrelationId() throws Exception {
        given(orderService.create(any(), anyString())).willAnswer(invocation -> {
            MDC.put("correlationId", invocation.getArgument(1, String.class));
            throw new PaymentGatewayException("PAYMENT_TIMEOUT", "Timeout while calling payment service");
        });

        mockMvc.perform(post("/orders").header("X-Correlation-Id", "corr-123")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{" + "\"customerId\":\"c1\",\"amount\":10,\"currency\":\"USD\"}"))
                .andExpect(status().isGatewayTimeout())
                .andExpect(jsonPath("$.code").value("PAYMENT_TIMEOUT"))
                .andExpect(jsonPath("$.correlationId").value("corr-123"));
    }

    @Test
    void validationErrorContainsCorrelationId() throws Exception {
        MDC.put("correlationId", "corr-456");
        mockMvc.perform(post("/orders").header("X-Correlation-Id", "corr-456")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{" + "\"customerId\":\"\",\"amount\":0,\"currency\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"))
                .andExpect(jsonPath("$.correlationId").value("corr-456"));
    }
}
