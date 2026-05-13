package com.playground.ordersservice.infra.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "orders")
public record RestClientsProperties(RestClients restClients) {

    public RestClientsProperties {
        if (restClients == null) {
            restClients = new RestClients(new TimeoutSettings(2_000, 3_000));
        }
    }

    public record RestClients(TimeoutSettings payments) {
        public RestClients {
            if (payments == null) {
                payments = new TimeoutSettings(2_000, 3_000);
            }
        }
    }

    public record TimeoutSettings(int connectTimeoutMs, int readTimeoutMs) {}
}
