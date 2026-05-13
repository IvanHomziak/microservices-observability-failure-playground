package com.playground.ordersservice.infra.http;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import com.playground.ordersservice.infra.config.RestClientsProperties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class PaymentClientTest {
    private RestTemplate restTemplate;
    private PaymentClient paymentClient;

    @BeforeEach
    void setUp() {
        restTemplate = mock(RestTemplate.class);
        var failures = new FailureScenariosProperties(false, false, false, false);
        var restClientsProperties = new RestClientsProperties(new RestClientsProperties.RestClients(
                new RestClientsProperties.RestClient("http://payments.internal:8090"),
                new RestClientsProperties.RestClient("unused")
        ));
        paymentClient = new PaymentClient(restTemplate, failures, restClientsProperties);
    }

    @Test
    void mapsAuthorizedToApprovedTrue() {
        when(restTemplate.postForEntity(eq("http://payments.internal:8090/payments/authorize"), any(), eq(PaymentAuthorizationResponse.class)))
                .thenReturn(ResponseEntity.ok(new PaymentAuthorizationResponse("id-1", "o-1", "AUTHORIZED")));
        assertThat(paymentClient.authorize("o-1", BigDecimal.TEN, "USD")).isTrue();
    }

    @Test
    void mapsDeclinedToApprovedFalse() {
        when(restTemplate.postForEntity(eq("http://payments.internal:8090/payments/authorize"), any(), eq(PaymentAuthorizationResponse.class)))
                .thenReturn(ResponseEntity.ok(new PaymentAuthorizationResponse("id-2", "o-2", "DECLINED")));
        assertThat(paymentClient.authorize("o-2", BigDecimal.ONE, "USD")).isFalse();
    }

    @Test
    void mapsUnknownStatusToPaymentInvalidResponse() {
        when(restTemplate.postForEntity(eq("http://payments.internal:8090/payments/authorize"), any(), eq(PaymentAuthorizationResponse.class)))
                .thenReturn(ResponseEntity.ok(new PaymentAuthorizationResponse("id-3", "o-3", "SOMETHING_ELSE")));
        assertThatThrownBy(() -> paymentClient.authorize("o-3", BigDecimal.ONE, "USD"))
                .isInstanceOf(PaymentGatewayException.class)
                .extracting("code").isEqualTo("PAYMENT_INVALID_RESPONSE");
    }

    @Test
    void mapsMissingStatusToPaymentInvalidResponse() {
        when(restTemplate.postForEntity(eq("http://payments.internal:8090/payments/authorize"), any(), eq(PaymentAuthorizationResponse.class)))
                .thenReturn(ResponseEntity.ok(new PaymentAuthorizationResponse("id-4", "o-4", null)));
        assertThatThrownBy(() -> paymentClient.authorize("o-4", BigDecimal.ONE, "USD"))
                .isInstanceOf(PaymentGatewayException.class)
                .extracting("code").isEqualTo("PAYMENT_INVALID_RESPONSE");
    }

    @Test
    void mapsResourceAccessExceptionToPaymentTimeout() {
        when(restTemplate.postForEntity(eq("http://payments.internal:8090/payments/authorize"), any(), eq(PaymentAuthorizationResponse.class)))
                .thenThrow(new ResourceAccessException("timeout"));
        assertThatThrownBy(() -> paymentClient.authorize("o-5", BigDecimal.ONE, "USD"))
                .isInstanceOf(PaymentGatewayException.class)
                .extracting("code").isEqualTo("PAYMENT_TIMEOUT");
    }
}
