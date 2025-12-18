package com.primeinterviews.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

/**
 * Prime Interviews API - Spring Boot Application
 *
 * A comprehensive backend service for interview scheduling and management.
 *
 * @version 2.0.0
 * @author Prime Interviews Team
 */
@SpringBootApplication
@EnableJpaAuditing
public class PrimeInterviewsApplication {

    public static void main(String[] args) {
        SpringApplication.run(PrimeInterviewsApplication.class, args);
    }
}
