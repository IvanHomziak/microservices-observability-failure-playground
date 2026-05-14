package com.playground.paymentsservice.api;

import com.playground.paymentsservice.app.PaymentsService;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationRequest;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationResponse;
import com.playground.paymentsservice.config.PaymentFailureSimulationProperties;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/payments")
public class PaymentsController {
    private static final Logger log = LoggerFactory.getLogger(PaymentsController.class);

    private final PaymentsService paymentsService;
    private final PaymentFailureSimulationProperties failureSimulationProperties;

    public PaymentsController(PaymentsService paymentsService, PaymentFailureSimulationProperties failureSimulationProperties) {
        this.paymentsService = paymentsService;
        this.failureSimulationProperties = failureSimulationProperties;
    }

    @PostMapping(path = "/authorize", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> authorize(@Valid @RequestBody PaymentAuthorizationRequest request,
                                       @RequestHeader(value = "X-Correlation-Id", required = false) String correlationId,
                                       @RequestHeader(value = "traceparent", required = false) String traceparent) {
        String inboundTraceparent = traceparent == null || traceparent.isBlank() ? "missing" : traceparent;
        log.info("operation=payment_authorize_received order_id={} correlation_id={} traceparent={}",
                request.orderId(), correlationId, inboundTraceparent);
        if (paymentsService.shouldReturnInvalidJson()) {
            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body("{\"paymentId\":\"broken\",\"status\":AUTHORIZED");
        }
        if (failureSimulationProperties.forcedStatusCode() == 500) {
            log.warn("operation=payment_failure_mode_triggered mode=forced-status-500 order_id={} correlation_id={} trace_id={}",
                    request.orderId(), correlationId, MDC.get("traceId"));
            return ResponseEntity.internalServerError().build();
        }

        PaymentAuthorizationResponse response = paymentsService.authorize(request);
        return ResponseEntity.ok(response);
    }
}
