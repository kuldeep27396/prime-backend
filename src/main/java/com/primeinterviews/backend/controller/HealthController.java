package com.primeinterviews.backend.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@RestController
@Tag(name = "Health", description = "Health check endpoints")
public class HealthController {

    @Value("${app.name}")
    private String appName;

    @Value("${app.version}")
    private String appVersion;

    @Value("${app.environment}")
    private String environment;

    @GetMapping("/")
    @Operation(
        summary = "Root endpoint",
        description = "Returns basic API information and operational status"
    )
    public ResponseEntity<Map<String, Object>> root() {
        Map<String, Object> response = new HashMap<>();
        response.put("message", appName + " v" + appVersion);
        response.put("status", "operational");
        response.put("docs", "/docs");
        response.put("health", "/health");
        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    @Operation(
        summary = "Health check",
        description = "Returns the health status of the API service"
    )
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "healthy");
        response.put("timestamp", Instant.now().toString());
        response.put("version", appVersion);
        response.put("environment", environment);
        response.put("database", "connected"); // Will be updated when DB is connected
        return ResponseEntity.ok(response);
    }
}
