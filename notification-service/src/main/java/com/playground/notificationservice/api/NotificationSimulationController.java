package com.playground.notificationservice.api;

import com.playground.notificationservice.app.FailureConfig;
import com.playground.notificationservice.app.FailureMode;
import com.playground.notificationservice.domain.NotificationRequestedEvent;
import com.playground.notificationservice.domain.PubSubPort;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/notifications")
public class NotificationSimulationController {
    private final PubSubPort pubSubPort;
    private final FailureConfig failureConfig;

    public NotificationSimulationController(PubSubPort pubSubPort, FailureConfig failureConfig) {
        this.pubSubPort = pubSubPort;
        this.failureConfig = failureConfig;
    }

    @PostMapping("/events")
    public ResponseEntity<Map<String, Object>> publish(@Valid @RequestBody NotificationRequestedEvent event) {
        String messageId = pubSubPort.publish("notification-events", event);
        return ResponseEntity.accepted().body(Map.of("messageId", messageId, "failureMode", failureConfig.getMode().name()));
    }

    @PutMapping("/failure-mode/{mode}")
    public Map<String, String> setFailureMode(@PathVariable FailureMode mode) {
        failureConfig.setMode(mode);
        return Map.of("failureMode", mode.name());
    }

    @GetMapping("/failure-mode")
    public Map<String, String> getFailureMode() {
        return Map.of("failureMode", failureConfig.getMode().name());
    }
}
