package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "session_analytics", indexes = {
    @Index(name = "idx_sa_session_id", columnList = "session_id"),
    @Index(name = "idx_sa_user_id", columnList = "user_id"),
    @Index(name = "idx_sa_mentor_id", columnList = "mentor_id"),
    @Index(name = "idx_sa_created_at", columnList = "created_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SessionAnalytics {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false, unique = true)
    private Session session;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "mentor_id", nullable = false)
    private Mentor mentor;

    @Column(name = "performance_score")
    private Integer performanceScore; // 0-100

    @Column(name = "technical_score")
    private Integer technicalScore; // 0-100

    @Column(name = "communication_score")
    private Integer communicationScore; // 0-100

    @Column(name = "problem_solving_score")
    private Integer problemSolvingScore; // 0-100

    @Column(name = "feedback_summary", columnDefinition = "TEXT")
    private String feedbackSummary;

    @Column(name = "key_improvements", columnDefinition = "jsonb")
    private String keyImprovements; // JSON array

    @Column(columnDefinition = "jsonb")
    private String strengths; // JSON array

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
