package com.playground.paymentsservice.api;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/payments")
public class PaymentsController {
    @PostMapping("/authorize")
    public Map<String, Object> authorize(@RequestBody Map<String, Object> request) {
        return Map.of("orderId", request.get("orderId"), "approved", true);
    }
}
