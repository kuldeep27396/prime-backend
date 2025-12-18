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
@Table(name = "skill_progression", indexes = {
    @Index(name = "idx_sp_user_id", columnList = "user_id"),
    @Index(name = "idx_sp_skill", columnList = "skill"),
    @Index(name = "idx_last_assessed_at", columnList = "last_assessed_at"),
    @Index(name = "idx_sp_created_at", columnList = "created_at"),
    @Index(name = "idx_sp_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SkillProgression {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, length = 255)
    private String skill;

    @Column(name = "initial_score")
    private Integer initialScore; // 0-100

    @Column(name = "current_score")
    private Integer currentScore; // 0-100

    @Column(name = "improvement_percentage", precision = 5, scale = 2)
    private BigDecimal improvementPercentage;

    @Column(name = "assessments_count")
    private Integer assessmentsCount = 0;

    @Column(name = "last_assessed_at")
    private LocalDateTime lastAssessedAt = LocalDateTime.now();

    @Column(name = "next_recommended_assessment")
    private LocalDateTime nextRecommendedAssessment;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
