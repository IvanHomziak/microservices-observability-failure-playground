package com.playground.ordersservice.infra;

import com.playground.ordersservice.infra.config.FailureScenariosProperties;
import com.playground.ordersservice.infra.config.RestClientsProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.web.client.RestTemplate;


import java.time.Duration;

@Configuration
@EnableConfigurationProperties({FailureScenariosProperties.class, RestClientsProperties.class})
public class AppConfig {
    @Bean
    RestTemplate restTemplate(RestTemplateBuilder builder, RestClientsProperties restClientsProperties, FailureScenariosProperties failureScenariosProperties) {
        RestClientsProperties.TimeoutSettings paymentsTimeouts = restClientsProperties.restClients().payments();
        return builder
                .setConnectTimeout(Duration.ofMillis(paymentsTimeouts.connectTimeoutMs()))
                .setReadTimeout(Duration.ofMillis(paymentsTimeouts.readTimeoutMs()))
                .additionalInterceptors(tracePropagationInterceptor(failureScenariosProperties))
                .build();
    }

    private ClientHttpRequestInterceptor tracePropagationInterceptor(FailureScenariosProperties failures) {
        return (request, body, execution) -> {
            if (failures.isTracingBreakPropagationToPayments()) {
                request.getHeaders().remove("traceparent");
                request.getHeaders().remove("tracestate");
                request.getHeaders().remove("b3");
                request.getHeaders().remove("X-B3-TraceId");
                request.getHeaders().remove("X-B3-SpanId");
                request.getHeaders().remove("X-B3-ParentSpanId");
                request.getHeaders().remove("X-B3-Sampled");
                request.getHeaders().remove("X-B3-Flags");
            }
            return execution.execute(request, body);
        };
    }
}
