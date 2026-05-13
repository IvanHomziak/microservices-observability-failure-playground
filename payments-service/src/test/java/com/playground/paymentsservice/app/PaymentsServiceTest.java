package com.playground.paymentsservice.app;

import com.playground.paymentsservice.app.dto.PaymentAuthorizationRequest;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationResponse;
import com.playground.paymentsservice.config.PaymentFailureSimulationProperties;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PaymentsServiceTest {
    @Test
    void shouldAuthorizeWhenNoFailureModesAreEnabled() {
        PaymentsService service = new PaymentsService(new PaymentFailureSimulationProperties(0L, 0, 0.0, false, false, false), new SimpleMeterRegistry());

        PaymentAuthorizationResponse response = service.authorize(new PaymentAuthorizationRequest("order-1", BigDecimal.TEN, "USD"));

        assertThat(response.orderId()).isEqualTo("order-1");
        assertThat(response.status()).isEqualTo("AUTHORIZED");
        assertThat(response.authorizationId()).isNotBlank();
    }

    @Test
    void shouldReturnDeclinedWhenDeclineModeEnabled() {
        PaymentsService service = new PaymentsService(new PaymentFailureSimulationProperties(0L, 0, 0.0, false, true, false), new SimpleMeterRegistry());

        PaymentAuthorizationResponse response = service.authorize(new PaymentAuthorizationRequest("order-2", BigDecimal.ONE, "USD"));

        assertThat(response.status()).isEqualTo("DECLINED");
    }

    @Test
    void shouldThrowConfiguredForcedStatus() {
        PaymentsService service = new PaymentsService(new PaymentFailureSimulationProperties(0L, 500, 0.0, false, false, false), new SimpleMeterRegistry());

        assertThatThrownBy(() -> service.authorize(new PaymentAuthorizationRequest("order-3", BigDecimal.ONE, "USD")))
                .isInstanceOf(ResponseStatusException.class)
                .satisfies(ex -> assertThat(((ResponseStatusException) ex).getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR));
    }
}
