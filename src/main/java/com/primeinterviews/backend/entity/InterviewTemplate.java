package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "interview_templates", indexes = {
    @Index(name = "idx_template_name", columnList = "name"),
    @Index(name = "idx_interview_type", columnList = "interview_type"),
    @Index(name = "idx_template_difficulty", columnList = "difficulty"),
    @Index(name = "idx_template_public", columnList = "is_public"),
    @Index(name = "idx_template_created_at", columnList = "created_at"),
    @Index(name = "idx_template_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class InterviewTemplate {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @Column(nullable = false, length = 255)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "interview_type", nullable = false, length = 100)
    private String interviewType; // technical, behavioral, system_design

    @Column(name = "duration_minutes", nullable = false)
    private Integer durationMinutes;

    @Column(columnDefinition = "jsonb")
    private String questions; // JSON array of question IDs

    @Column(columnDefinition = "jsonb")
    private String companies; // JSON array

    @Column(length = 50)
    private String difficulty;

    @Column(name = "is_public")
    private Boolean isPublic = true;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by")
    private User creator;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
