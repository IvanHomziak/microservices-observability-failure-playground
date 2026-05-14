package com.playground.auditservice.api;

import com.playground.auditservice.domain.AuditEvent;
import com.playground.auditservice.domain.AuditRecorder;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/audit/events")
public class AuditController {
    private final AuditRecorder auditRecorder;

    public AuditController(AuditRecorder auditRecorder) {
        this.auditRecorder = auditRecorder;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.ACCEPTED)
    public void record(@RequestBody AuditEvent event) {
        auditRecorder.record(event, "http");
    }
}
