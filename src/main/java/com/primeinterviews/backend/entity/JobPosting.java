package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "job_postings", indexes = {
    @Index(name = "idx_job_company_id", columnList = "company_id"),
    @Index(name = "idx_job_title", columnList = "title"),
    @Index(name = "idx_job_active", columnList = "is_active"),
    @Index(name = "idx_posted_at", columnList = "posted_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class JobPosting {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "company_id", nullable = false)
    private Company company;

    @Column(nullable = false, length = 255)
    private String title;

    @Column(length = 255)
    private String department;

    @Column(length = 255)
    private String location;

    @Column(name = "job_type", length = 100)
    private String jobType; // Full-time, Part-time, Contract

    @Column(name = "experience_level", length = 100)
    private String experienceLevel; // Entry, Mid, Senior

    @Column(name = "salary_min", precision = 10, scale = 2)
    private BigDecimal salaryMin;

    @Column(name = "salary_max", precision = 10, scale = 2)
    private BigDecimal salaryMax;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(columnDefinition = "jsonb")
    private String requirements; // JSON array

    @Column(name = "skills_required", columnDefinition = "jsonb")
    private String skillsRequired; // JSON array

    @Column(name = "is_active")
    private Boolean isActive = true;

    @Column(name = "posted_at")
    private LocalDateTime postedAt = LocalDateTime.now();

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;
}
