package com.playground.ordersservice.infra;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;

import java.util.concurrent.TimeUnit;

@Component
public class DatabaseOperationLatencySimulator {
    private static final Logger log = LoggerFactory.getLogger(DatabaseOperationLatencySimulator.class);

    private final FailureScenariosProperties failures;
    private final Timer operationDuration;
    private final Tracer tracer;

    public DatabaseOperationLatencySimulator(FailureScenariosProperties failures,
                                             MeterRegistry meterRegistry,
                                             Tracer tracer) {
        this.failures = failures;
        this.operationDuration = meterRegistry.timer("orders.database.operation.duration");
        this.tracer = tracer;
    }

    public void simulate(String orderId) {
        long started = System.nanoTime();
        String correlationId = MDC.get("correlation_id");
        log.info("operation=db_query_started order_id={} correlation_id={} duration_ms=0", orderId, correlationId);

        Span span = tracer.nextSpan().name("orders.db.simulated.query").start();
        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            if (failures.getDatabase().isSlowQueryEnabled() && failures.getDatabase().getSlowQueryDelayMs() > 0) {
                long delayMs = failures.getDatabase().getSlowQueryDelayMs();
                try {
                    Thread.sleep(delayMs);
                } catch (InterruptedException ex) {
                    Thread.currentThread().interrupt();
                }
                long slowDurationMs = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started);
                log.info("operation=db_query_slow_simulated order_id={} correlation_id={} duration_ms={}",
                        orderId, correlationId, slowDurationMs);
            }
        } finally {
            span.end();
            long durationMs = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started);
            operationDuration.record(durationMs, TimeUnit.MILLISECONDS);
            log.info("operation=db_query_completed order_id={} correlation_id={} duration_ms={}",
                    orderId, correlationId, durationMs);
        }
    }
}
