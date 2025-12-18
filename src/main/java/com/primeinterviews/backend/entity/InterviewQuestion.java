package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "interview_questions", indexes = {
    @Index(name = "idx_question_type", columnList = "question_type"),
    @Index(name = "idx_question_difficulty", columnList = "difficulty"),
    @Index(name = "idx_category", columnList = "category"),
    @Index(name = "idx_question_active", columnList = "is_active"),
    @Index(name = "idx_question_created_at", columnList = "created_at"),
    @Index(name = "idx_question_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class InterviewQuestion {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String question;

    @Column(name = "question_type", nullable = false, length = 100)
    private String questionType; // technical, behavioral, system_design

    @Column(length = 50)
    private String difficulty; // easy, medium, hard

    @Column(length = 255)
    private String category;

    @Column(name = "skills_tested", columnDefinition = "jsonb")
    private String skillsTested; // JSON array

    @Column(name = "expected_answer", columnDefinition = "TEXT")
    private String expectedAnswer;

    @Column(name = "follow_up_questions", columnDefinition = "jsonb")
    private String followUpQuestions; // JSON array

    @Column(name = "companies_asked_at", columnDefinition = "jsonb")
    private String companiesAskedAt; // JSON array

    @Column(name = "time_limit_minutes")
    private Integer timeLimitMinutes;

    @Column(name = "is_active")
    private Boolean isActive = true;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "question", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<UserResponse> userResponses;
}
