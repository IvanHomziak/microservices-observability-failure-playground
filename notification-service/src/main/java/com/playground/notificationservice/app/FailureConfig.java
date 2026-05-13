package com.playground.notificationservice.app;

import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicReference;

@Component
public class FailureConfig {
    private final AtomicReference<FailureMode> mode = new AtomicReference<>(FailureMode.NONE);

    public FailureMode getMode() {
        return mode.get();
    }

    public void setMode(FailureMode failureMode) {
        this.mode.set(failureMode);
    }
}
