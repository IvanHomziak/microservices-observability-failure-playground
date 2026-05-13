package com.playground.notificationservice.app;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicReference;

@Component
public class FailureConfig {
    private final AtomicReference<FailureMode> mode = new AtomicReference<>(FailureMode.NONE);
    private final boolean publishFailureEnabled;

    public FailureConfig(@Value("${failure-simulation.pubsub.publish-failure-enabled:false}") boolean publishFailureEnabled) {
        this.publishFailureEnabled = publishFailureEnabled;
    }

    public FailureMode getMode() {
        if (publishFailureEnabled) {
            return FailureMode.PUBLISH_FAILURE;
        }
        return mode.get();
    }

    public void setMode(FailureMode failureMode) {
        this.mode.set(failureMode);
    }
}
