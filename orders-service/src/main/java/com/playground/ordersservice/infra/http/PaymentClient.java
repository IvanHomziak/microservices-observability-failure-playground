package com.playground.ordersservice.infra.http;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.util.Map;

@Component
public class PaymentClient {
    private static final Logger log = LoggerFactory.getLogger(PaymentClient.class);
    private final RestTemplate restTemplate;
    private final FailureScenariosProperties failures;

    public PaymentClient(RestTemplate restTemplate, FailureScenariosProperties failures) {
        this.restTemplate = restTemplate;
        this.failures = failures;
    }

    public boolean authorize(String orderId, BigDecimal amount, String currency) {
        log.info("operation=payment_authorization_started event_id=payment_authorization_started order_id={} amount={} currency={}", orderId, amount, currency);
        if (failures.isPaymentTimeout()) {
            throw new PaymentGatewayException("PAYMENT_TIMEOUT", "Simulated payment timeout");
        }
        if (failures.isPaymentConnectionFailure()) {
            throw new PaymentGatewayException("PAYMENT_CONNECTION_FAILURE", "Simulated payment connection failure");
        }

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    "http://localhost:8082/payments/authorize",
                    new HttpEntity<>(Map.of("orderId", orderId, "amount", amount, "currency", currency)),
                    Map.class
            );

            HttpStatusCode status = response.getStatusCode();
            if (status.is5xxServerError()) {
                throw new PaymentGatewayException("PAYMENT_5XX", "Payment service returned 5xx status");
            }

            Map body = response.getBody();
            if (failures.isPaymentInvalidResponse() || body == null || !body.containsKey("approved")) {
                throw new PaymentGatewayException("PAYMENT_INVALID_RESPONSE", "Payment service returned invalid response");
            }

            boolean approved = Boolean.TRUE.equals(body.get("approved"));
            if (approved) {
                log.info("operation=payment_authorization_succeeded event_id=payment_authorization_succeeded order_id={}", orderId);
            } else {
                log.warn("operation=payment_authorization_failed event_id=payment_authorization_declined order_id={}", orderId);
            }
            return approved;
        } catch (ResourceAccessException e) {
            log.error("operation=resttemplate_timeout event_id=payments_authorization_timeout order_id={} exception_type={} exception_message={}",
                    orderId, e.getClass().getSimpleName(), e.getMessage(), e);
            throw new PaymentGatewayException("PAYMENT_TIMEOUT", "Timeout while calling payment service", e);
        } catch (RestClientResponseException e) {
            if (e.getStatusCode().is5xxServerError()) {
                throw new PaymentGatewayException("PAYMENT_5XX", "Payment service returned 5xx status", e);
            }
            throw new PaymentGatewayException("PAYMENT_INVALID_RESPONSE", "Unexpected payment response", e);
        }
    }
}
