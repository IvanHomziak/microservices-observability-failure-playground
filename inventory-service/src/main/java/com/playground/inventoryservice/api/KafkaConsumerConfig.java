package com.playground.inventoryservice.api;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.TopicPartition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.util.backoff.FixedBackOff;

@Configuration
public class KafkaConsumerConfig {

    private static final Logger log = LoggerFactory.getLogger(KafkaConsumerConfig.class);

    @Bean
    public DefaultErrorHandler kafkaErrorHandler(
            KafkaTemplate<Object, Object> kafkaTemplate,
            @Value("${app.kafka.topics.order-created-dlq}") String dlqTopic,
            @Value("${app.kafka.retry.interval-ms}") long retryIntervalMs,
            @Value("${app.kafka.retry.max-attempts}") long retryAttempts
    ) {
        DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(
                kafkaTemplate,
                (record, ex) -> new TopicPartition(dlqTopic, record.partition())
        );

        DefaultErrorHandler errorHandler = new DefaultErrorHandler(
                recoverer,
                new FixedBackOff(retryIntervalMs, retryAttempts)
        );

        errorHandler.setRetryListeners((ConsumerRecord<?, ?> record, Exception ex, int deliveryAttempt) ->
                log.warn("Retry attempt={} topic={} partition={} offset={} key={} cause={}",
                        deliveryAttempt,
                        record.topic(),
                        record.partition(),
                        record.offset(),
                        record.key(),
                        ex.getClass().getSimpleName())
        );

        return errorHandler;
    }
}
