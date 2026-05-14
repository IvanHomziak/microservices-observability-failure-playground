package com.playground.inventoryservice.api;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.header.internals.RecordHeader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.util.backoff.FixedBackOff;

import java.nio.charset.StandardCharsets;

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

        recoverer.setHeadersFunction((record, ex) -> {
            var headers = record.headers();
            headers.add(new RecordHeader("error_reason", ex.getMessage().getBytes(StandardCharsets.UTF_8)));
            headers.add(new RecordHeader("error_type", ex.getClass().getSimpleName().getBytes(StandardCharsets.UTF_8)));
            headers.add(new RecordHeader("original_topic", record.topic().getBytes(StandardCharsets.UTF_8)));
            headers.add(new RecordHeader("original_partition", String.valueOf(record.partition()).getBytes(StandardCharsets.UTF_8)));
            headers.add(new RecordHeader("original_offset", String.valueOf(record.offset()).getBytes(StandardCharsets.UTF_8)));
            return headers;
        });

        DefaultErrorHandler errorHandler = new DefaultErrorHandler(
                (record, ex) -> {
                    recoverer.accept(record, ex);
                    log.error("operation=kafka_dlq_published topic={} partition={} offset={} event_id={} order_id={} correlation_id={} exception_type={} exception_message={}",
                            record.topic(),
                            record.partition(),
                            record.offset(),
                            extractField(record, "eventId"),
                            extractField(record, "orderId"),
                            extractCorrelationId(record),
                            ex.getClass().getSimpleName(),
                            ex.getMessage());
                },
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

    private static String extractCorrelationId(ConsumerRecord<?, ?> record) {
        var header = record.headers().lastHeader("correlation_id");
        if (header != null) {
            return new String(header.value(), StandardCharsets.UTF_8);
        }
        return extractField(record, "correlationId");
    }

    private static String extractField(ConsumerRecord<?, ?> record, String fieldName) {
        Object value = record.value();
        if (value instanceof OrderCreatedEvent event) {
            return switch (fieldName) {
                case "eventId" -> event.eventId();
                case "orderId" -> event.orderId();
                case "correlationId" -> event.correlationId();
                default -> null;
            };
        }
        return null;
    }
}
