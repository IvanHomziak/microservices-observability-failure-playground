package com.playground.apigateway.config;

import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.UUID;

@Component
public class CorrelationIdRestTemplateInterceptor implements ClientHttpRequestInterceptor {

    private static final Logger log = LoggerFactory.getLogger(CorrelationIdRestTemplateInterceptor.class);
    private final Tracer tracer;

    public CorrelationIdRestTemplateInterceptor(Tracer tracer) {
        this.tracer = tracer;
    }

    @Override
    public ClientHttpResponse intercept(HttpRequest request, byte[] body, ClientHttpRequestExecution execution) throws IOException {
        String correlationId = MDC.get(CorrelationIdLoggingFilter.CORRELATION_ID_KEY);
        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }
        request.getHeaders().set(CorrelationIdLoggingFilter.CORRELATION_ID_HEADER, correlationId);

        long startedAt = System.currentTimeMillis();
        ClientHttpResponse response = execution.execute(request, body);
        long durationMs = System.currentTimeMillis() - startedAt;

        Span currentSpan = tracer.currentSpan();
        String traceId = currentSpan != null ? currentSpan.context().traceId() : "";
        String spanId = currentSpan != null ? currentSpan.context().spanId() : "";

        log.info(
                "outbound method={} path={} status={} duration_ms={} correlation_id={} trace_id={} span_id={}",
                request.getMethod(),
                request.getURI().getPath(),
                response.getStatusCode().value(),
                durationMs,
                correlationId,
                traceId,
                spanId
        );
        return response;
    }
}
