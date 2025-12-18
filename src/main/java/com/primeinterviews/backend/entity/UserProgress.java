package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "user_progress", indexes = {
    @Index(name = "idx_progress_user_id", columnList = "user_id"),
    @Index(name = "idx_progress_resource_id", columnList = "resource_id"),
    @Index(name = "idx_progress_status", columnList = "status")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserProgress {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "resource_id", nullable = false)
    private LearningResource resource;

    @Column(length = 50)
    private String status = "not_started"; // not_started, in_progress, completed

    @Column(name = "progress_percentage")
    private Integer progressPercentage = 0;

    @Column(name = "started_at")
    private LocalDateTime startedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @Column(name = "time_spent_minutes")
    private Integer timeSpentMinutes = 0;

    private Integer rating; // 1-5

    @Column(columnDefinition = "TEXT")
    private String notes;
}
