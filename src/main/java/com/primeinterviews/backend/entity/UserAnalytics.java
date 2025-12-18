package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "user_analytics", indexes = {
    @Index(name = "idx_analytics_user_id", columnList = "user_id"),
    @Index(name = "idx_last_activity_at", columnList = "last_activity_at"),
    @Index(name = "idx_analytics_created_at", columnList = "created_at"),
    @Index(name = "idx_analytics_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserAnalytics {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "total_sessions")
    private Integer totalSessions = 0;

    @Column(name = "completed_sessions")
    private Integer completedSessions = 0;

    @Column(name = "average_rating", precision = 3, scale = 2)
    private BigDecimal averageRating = BigDecimal.ZERO;

    @Column(name = "total_time_spent_minutes")
    private Integer totalTimeSpentMinutes = 0;

    @Column(name = "skills_improved", columnDefinition = "jsonb")
    private String skillsImproved; // JSON array with improvement data

    @Column(name = "companies_interviewed_with", columnDefinition = "jsonb")
    private String companiesInterviewedWith; // JSON array

    @Column(name = "session_history", columnDefinition = "jsonb")
    private String sessionHistory; // JSON detailed session performance data

    @Column(name = "streak_days")
    private Integer streakDays = 0;

    @Column(name = "last_activity_at")
    private LocalDateTime lastActivityAt = LocalDateTime.now();

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
