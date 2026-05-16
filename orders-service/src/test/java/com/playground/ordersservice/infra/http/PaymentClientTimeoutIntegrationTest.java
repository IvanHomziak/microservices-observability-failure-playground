package com.playground.ordersservice.infra.http;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import com.playground.ordersservice.infra.config.RestClientsProperties;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class PaymentClientTimeoutIntegrationTest {

    @Test
    void shouldMapResourceAccessExceptionToPaymentTimeout() {
        RestTemplate restTemplate = mock(RestTemplate.class);
        FailureScenariosProperties failures = new FailureScenariosProperties();
        RestClientsProperties restClientsProperties = new RestClientsProperties(
                new RestClientsProperties.RestClients(
                        new RestClientsProperties.Payments("http://localhost:8082", 2000, 3000)
                )
        );
        PaymentClient client = new PaymentClient(restTemplate, failures, restClientsProperties);

        when(restTemplate.postForEntity(eq("http://localhost:8082/payments/authorize"), any(), eq(PaymentAuthorizationResponse.class)))
                .thenThrow(new ResourceAccessException("Read timed out"));

        assertThatThrownBy(() -> client.authorize("order-1", BigDecimal.ONE, "USD"))
                .isInstanceOf(PaymentGatewayException.class)
                .satisfies(ex -> assertThat(((PaymentGatewayException) ex).getCode()).isEqualTo("PAYMENT_TIMEOUT"));
    }
}
