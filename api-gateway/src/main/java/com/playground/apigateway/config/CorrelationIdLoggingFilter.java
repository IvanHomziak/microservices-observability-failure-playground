package com.playground.apigateway.config;

import io.micrometer.tracing.Tracer;
import io.micrometer.tracing.Span;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

@Component
public class CorrelationIdLoggingFilter extends OncePerRequestFilter {

    public static final String CORRELATION_ID_HEADER = "X-Correlation-Id";
    public static final String CORRELATION_ID_KEY = "correlation_id";
    private static final Logger log = LoggerFactory.getLogger(CorrelationIdLoggingFilter.class);

    private final Tracer tracer;
    private final String serviceName;
    private final String environment;

    public CorrelationIdLoggingFilter(Tracer tracer,
                                      @Value("${spring.application.name:api-gateway}") String serviceName,
                                      @Value("${app.environment:local}") String environment) {
        this.tracer = tracer;
        this.serviceName = serviceName;
        this.environment = environment;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String correlationId = request.getHeader(CORRELATION_ID_HEADER);
        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }

        response.setHeader(CORRELATION_ID_HEADER, correlationId);
        MDC.put(CORRELATION_ID_KEY, correlationId);

        long startedAt = System.currentTimeMillis();
        try {
            filterChain.doFilter(request, response);
        } finally {
            long durationMs = System.currentTimeMillis() - startedAt;
            Span currentSpan = tracer.currentSpan();
            String traceId = currentSpan != null ? currentSpan.context().traceId() : "";
            String spanId = currentSpan != null ? currentSpan.context().spanId() : "";

            log.info(
                    "event_id=inbound-http-request operation=inbound_http_request service={} environment={} method={} path={} status={} duration_ms={} correlation_id={} trace_id={} span_id={} request_id={}",
                    serviceName,
                    environment,
                    request.getMethod(),
                    request.getRequestURI(),
                    response.getStatus(),
                    durationMs,
                    correlationId,
                    traceId,
                    spanId,
                    correlationId
            );
            MDC.remove(CORRELATION_ID_KEY);
        }
    }
}
