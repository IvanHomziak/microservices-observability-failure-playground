package com.playground.ordersservice.app;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static com.playground.ordersservice.app.OrderRiskClassifier.RiskLevel.HIGH;
import static com.playground.ordersservice.app.OrderRiskClassifier.RiskLevel.LOW;
import static com.playground.ordersservice.app.OrderRiskClassifier.RiskLevel.MEDIUM;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class OrderRiskClassifierTest {

    private final OrderRiskClassifier classifier = new OrderRiskClassifier();

    @Test
    void shouldClassifyLowRiskOrderWhenAmountIsSmallAndCurrencyIsNotSpecial() {
        assertEquals(LOW, classifier.classify(new BigDecimal("25.50"), "EUR"));
    }

    @Test
    void shouldClassifyMediumRiskOrderWhenAmountReachesMediumThreshold() {
        assertEquals(MEDIUM, classifier.classify(new BigDecimal("500.00"), "EUR"));
    }

    @Test
    void shouldClassifyMediumRiskOrderWhenCurrencyIsUsd() {
        assertEquals(MEDIUM, classifier.classify(new BigDecimal("10.00"), "usd"));
    }

    @Test
    void shouldClassifyHighRiskOrderWhenAmountReachesHighThreshold() {
        assertEquals(HIGH, classifier.classify(new BigDecimal("1000.00"), "EUR"));
    }

    @Test
    void shouldClassifyHighRiskOrderWhenCurrencyIsBtc() {
        assertEquals(HIGH, classifier.classify(new BigDecimal("1.00"), "btc"));
    }

    @Test
    void shouldRejectNegativeAmount() {
        IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> classifier.classify(new BigDecimal("-1.00"), "EUR")
        );

        assertEquals("amount must not be negative", exception.getMessage());
    }

    @Test
    void shouldRejectBlankCurrency() {
        IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> classifier.classify(new BigDecimal("1.00"), "   ")
        );

        assertEquals("currency must not be blank", exception.getMessage());
    }

    @Test
    void shouldRejectNullAmount() {
        NullPointerException exception = assertThrows(
                NullPointerException.class,
                () -> classifier.classify(null, "EUR")
        );

        assertEquals("amount must not be null", exception.getMessage());
    }

    @Test
    void shouldRejectNullCurrency() {
        NullPointerException exception = assertThrows(
                NullPointerException.class,
                () -> classifier.classify(new BigDecimal("1.00"), null)
        );

        assertEquals("currency must not be null", exception.getMessage());
    }
}