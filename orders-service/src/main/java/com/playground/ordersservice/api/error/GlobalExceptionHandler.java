package com.playground.ordersservice.api.error;

import com.playground.ordersservice.infra.http.PaymentGatewayException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.slf4j.MDC;

import java.time.Instant;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
        return ResponseEntity.badRequest().body(new ApiError("VALIDATION_ERROR", "Invalid order request", correlationId(), Instant.now()));
    }

    @ExceptionHandler(PaymentGatewayException.class)
    public ResponseEntity<ApiError> handlePayment(PaymentGatewayException ex) {
        HttpStatus status = switch (ex.getCode()) {
            case "PAYMENT_TIMEOUT" -> HttpStatus.GATEWAY_TIMEOUT;
            case "PAYMENT_CONNECTION_FAILURE" -> HttpStatus.SERVICE_UNAVAILABLE;
            case "PAYMENT_5XX" -> HttpStatus.BAD_GATEWAY;
            case "PAYMENT_INVALID_RESPONSE" -> HttpStatus.BAD_GATEWAY;
            default -> HttpStatus.INTERNAL_SERVER_ERROR;
        };
        return ResponseEntity.status(status).body(new ApiError(ex.getCode(), ex.getMessage(), correlationId(), Instant.now()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleGeneric(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new ApiError("INTERNAL_ERROR", ex.getMessage(), correlationId(), Instant.now()));
    }

    private String correlationId() {
        return MDC.get("correlationId");
    }
}
