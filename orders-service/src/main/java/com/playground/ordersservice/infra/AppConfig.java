package com.playground.ordersservice.infra;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import com.playground.ordersservice.infra.config.RestClientsProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
@EnableConfigurationProperties({FailureScenariosProperties.class, RestClientsProperties.class})
public class AppConfig {
    @Bean
    RestTemplate restTemplate(RestTemplateBuilder builder, RestClientsProperties restClientsProperties) {
        RestClientsProperties.TimeoutSettings paymentsTimeouts = restClientsProperties.restClients().payments();
        return builder
                .setConnectTimeout(Duration.ofMillis(paymentsTimeouts.connectTimeoutMs()))
                .setReadTimeout(Duration.ofMillis(paymentsTimeouts.readTimeoutMs()))
                .build();
    }
}
