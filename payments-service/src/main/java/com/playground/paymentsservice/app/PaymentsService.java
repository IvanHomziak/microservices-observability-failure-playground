package com.playground.paymentsservice.app;

import com.playground.paymentsservice.app.dto.PaymentAuthorizationRequest;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationResponse;
import com.playground.paymentsservice.config.PaymentFailureSimulationProperties;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

@Service
public class PaymentsService {

    private static final Logger log = LoggerFactory.getLogger(PaymentsService.class);
    private final PaymentFailureSimulationProperties properties;
    private final Counter authorizationCounter;
    private final Counter failureCounter;

    public PaymentsService(PaymentFailureSimulationProperties properties, MeterRegistry meterRegistry) {
        this.properties = properties;
        this.authorizationCounter = meterRegistry.counter("payments.authorization.total");
        this.failureCounter = meterRegistry.counter("payments.authorization.failures.total");
    }

    public boolean shouldReturnInvalidJson() {
        if (properties.invalidJsonEnabled()) {
            registerFailure("invalid-json");
            return true;
        }
        return false;
    }

    public PaymentAuthorizationResponse authorize(PaymentAuthorizationRequest request) {
        authorizationCounter.increment();
        simulateDelay();
        simulateForcedStatus();
        simulateTimeout();
        simulateRandomFailure();

        if (properties.declineEnabled()) {
            registerFailure("declined");
            return new PaymentAuthorizationResponse(UUID.randomUUID().toString(), request.orderId(), "DECLINED");
        }

        log.info("event=payment_authorized orderId={} amount={} currency={} status=AUTHORIZED",
                request.orderId(), request.amount(), request.currency());

        return new PaymentAuthorizationResponse(UUID.randomUUID().toString(), request.orderId(), "AUTHORIZED");
    }

    private void simulateDelay() {
        if (properties.delayMs() > 0) {
            log.warn("event=payment_failure_mode_triggered mode=fixed-delay delayMs={}", properties.delayMs());
            sleep(properties.delayMs());
        }
    }

    private void simulateForcedStatus() {
        if (properties.forcedStatusCode() == 500 || properties.forcedStatusCode() == 503) {
            registerFailure("forced-status-" + properties.forcedStatusCode());
            throw new ResponseStatusException(HttpStatus.valueOf(properties.forcedStatusCode()), "Forced status simulation");
        }
    }

    private void simulateTimeout() {
        if (properties.timeoutEnabled()) {
            registerFailure("timeout");
            sleep(30_000L);
            throw new ResponseStatusException(HttpStatus.GATEWAY_TIMEOUT, "Timeout simulation");
        }
    }

    private void simulateRandomFailure() {
        if (properties.failureRate() > 0.0) {
            double draw = ThreadLocalRandom.current().nextDouble();
            if (draw < properties.failureRate()) {
                registerFailure("random-failure");
                throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Random failure simulation");
            }
        }
    }

    private void registerFailure(String mode) {
        failureCounter.increment();
        log.warn("event=payment_failure_mode_triggered mode={}", mode);
    }

    private void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Interrupted during simulation");
        }
    }
}
