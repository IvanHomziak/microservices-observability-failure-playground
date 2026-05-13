package com.playground.paymentsservice.api;

import com.playground.paymentsservice.app.PaymentsService;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationRequest;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(PaymentsController.class)
class PaymentsControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean PaymentsService paymentsService;

    @Test
    void returnsBrokenJsonWhenInvalidJsonModeEnabled() throws Exception {
        given(paymentsService.shouldReturnInvalidJson()).willReturn(true);

        mockMvc.perform(post("/payments/authorize").contentType(MediaType.APPLICATION_JSON)
                        .content("{" + "\"orderId\":\"order-1\",\"amount\":10,\"currency\":\"USD\"}"))
                .andExpect(status().isOk())
                .andExpect(content().string("{\"paymentId\":\"broken\",\"status\":AUTHORIZED"));
    }

    @Test
    void returnsAuthorizationResponseWhenInvalidJsonModeDisabled() throws Exception {
        given(paymentsService.shouldReturnInvalidJson()).willReturn(false);
        given(paymentsService.authorize(any(PaymentAuthorizationRequest.class)))
                .willReturn(new PaymentAuthorizationResponse("auth-1", "order-1", "AUTHORIZED"));

        mockMvc.perform(post("/payments/authorize").contentType(MediaType.APPLICATION_JSON)
                        .content("{" + "\"orderId\":\"order-1\",\"amount\":10,\"currency\":\"USD\"}"))
                .andExpect(status().isOk())
                .andExpect(content().json("{" + "\"authorizationId\":\"auth-1\",\"orderId\":\"order-1\",\"status\":\"AUTHORIZED\"}"));
    }
}
