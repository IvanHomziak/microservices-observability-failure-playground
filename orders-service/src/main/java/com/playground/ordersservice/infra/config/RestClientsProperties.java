package com.playground.ordersservice.infra.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "orders")
public record RestClientsProperties(RestClients restClients) {

    public RestClientsProperties {
        if (restClients == null) {
            restClients = new RestClients(new Payments("http://localhost:8082", 2_000, 3_000));
        }
    }

    public record RestClients(Payments payments) {
        public RestClients {
            if (payments == null) {
                payments = new Payments("http://localhost:8082", 2_000, 3_000);
            }
        }
    }

    public record Payments(String baseUrl, int connectTimeoutMs, int readTimeoutMs) {}
}
