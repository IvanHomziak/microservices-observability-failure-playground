package com.playground.paymentsservice.api;

import com.playground.paymentsservice.app.PaymentsService;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationRequest;
import com.playground.paymentsservice.app.dto.PaymentAuthorizationResponse;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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

    public PaymentsController(PaymentsService paymentsService) {
        this.paymentsService = paymentsService;
    }

    @PostMapping(path = "/authorize", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> authorize(@Valid @RequestBody PaymentAuthorizationRequest request,
                                       @RequestHeader(value = "X-Correlation-Id", required = false) String correlationId,
                                       @RequestHeader(value = "traceparent", required = false) String traceparent) {
        log.info("operation=payment_authorize_received order_id={} correlation_id={} traceparent={}",
                request.orderId(), correlationId, traceparent);
        if (paymentsService.shouldReturnInvalidJson()) {
            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body("{\"paymentId\":\"broken\",\"status\":AUTHORIZED");
        }

        PaymentAuthorizationResponse response = paymentsService.authorize(request);
        return ResponseEntity.ok(response);
    }
}
