package com.playground.ordersservice.infra.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "orders.failures")
public class FailureScenariosProperties {
    private final DatabaseFailureSimulation database = new DatabaseFailureSimulation();
    private boolean paymentTimeout;
    private boolean paymentConnectionFailure;
    private boolean paymentInvalidResponse;
    private boolean publishKafkaFailure;
    private boolean publishNotificationFailure;
    private boolean tracingBreakPropagationToPayments;

    public DatabaseFailureSimulation getDatabase() { return database; }

    public static class DatabaseFailureSimulation {
        private boolean slowQueryEnabled;
        private long slowQueryDelayMs;

        public boolean isSlowQueryEnabled() { return slowQueryEnabled; }
        public void setSlowQueryEnabled(boolean slowQueryEnabled) { this.slowQueryEnabled = slowQueryEnabled; }
        public long getSlowQueryDelayMs() { return slowQueryDelayMs; }
        public void setSlowQueryDelayMs(long slowQueryDelayMs) { this.slowQueryDelayMs = slowQueryDelayMs; }
    }

    public boolean isPaymentTimeout() { return paymentTimeout; }
    public void setPaymentTimeout(boolean paymentTimeout) { this.paymentTimeout = paymentTimeout; }
    public boolean isPaymentConnectionFailure() { return paymentConnectionFailure; }
    public void setPaymentConnectionFailure(boolean paymentConnectionFailure) { this.paymentConnectionFailure = paymentConnectionFailure; }
    public boolean isPaymentInvalidResponse() { return paymentInvalidResponse; }
    public void setPaymentInvalidResponse(boolean paymentInvalidResponse) { this.paymentInvalidResponse = paymentInvalidResponse; }
    public boolean isPublishKafkaFailure() { return publishKafkaFailure; }
    public void setPublishKafkaFailure(boolean publishKafkaFailure) { this.publishKafkaFailure = publishKafkaFailure; }
    public boolean isPublishNotificationFailure() { return publishNotificationFailure; }
    public void setPublishNotificationFailure(boolean publishNotificationFailure) { this.publishNotificationFailure = publishNotificationFailure; }
    public boolean isTracingBreakPropagationToPayments() { return tracingBreakPropagationToPayments; }
    public void setTracingBreakPropagationToPayments(boolean tracingBreakPropagationToPayments) { this.tracingBreakPropagationToPayments = tracingBreakPropagationToPayments; }
}
