package com.playground.ordersservice.infra.http;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import com.playground.ordersservice.infra.config.RestClientsProperties;
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
    private final String paymentsBaseUrl;

    public PaymentClient(RestTemplate restTemplate, FailureScenariosProperties failures, RestClientsProperties restClientsProperties) {
        this.restTemplate = restTemplate;
        this.failures = failures;
        this.paymentsBaseUrl = restClientsProperties.restClients().payments().baseUrl();
    }

    public boolean authorize(String orderId, BigDecimal amount, String currency) {
        log.info("operation=payment_authorization_started event_id=payment_authorization_started order_id={} amount={} currency={}", orderId, amount, currency);
        if (failures.isPaymentTimeout()) throw new PaymentGatewayException("PAYMENT_TIMEOUT", "Simulated payment timeout");
        if (failures.isPaymentConnectionFailure()) throw new PaymentGatewayException("PAYMENT_CONNECTION_FAILURE", "Simulated payment connection failure");

        try {
            ResponseEntity<PaymentAuthorizationResponse> response = restTemplate.postForEntity(
                    paymentsBaseUrl + "/payments/authorize",
                    new HttpEntity<>(Map.of("orderId", orderId, "amount", amount, "currency", currency)),
                    PaymentAuthorizationResponse.class
            );

            HttpStatusCode statusCode = response.getStatusCode();
            if (statusCode.is5xxServerError()) throw new PaymentGatewayException("PAYMENT_5XX", "Payment service returned 5xx status");

            PaymentAuthorizationResponse body = response.getBody();
            if (failures.isPaymentInvalidResponse() || body == null || body.status() == null) {
                throw new PaymentGatewayException("PAYMENT_INVALID_RESPONSE", "Payment service returned invalid response");
            }

            return switch (body.status()) {
                case "AUTHORIZED" -> true;
                case "DECLINED" -> false;
                default -> throw new PaymentGatewayException("PAYMENT_INVALID_RESPONSE", "Unknown payment status: " + body.status());
            };
        } catch (ResourceAccessException e) {
            throw new PaymentGatewayException("PAYMENT_TIMEOUT", "Timeout while calling payment service", e);
        } catch (RestClientResponseException e) {
            if (e.getStatusCode().is5xxServerError()) throw new PaymentGatewayException("PAYMENT_5XX", "Payment service returned 5xx status", e);
            throw new PaymentGatewayException("PAYMENT_INVALID_RESPONSE", "Unexpected payment response", e);
        }
    }
}
