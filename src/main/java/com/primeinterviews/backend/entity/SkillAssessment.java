package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "skill_assessments", indexes = {
    @Index(name = "idx_skill_user_id", columnList = "user_id"),
    @Index(name = "idx_skill_name", columnList = "skill"),
    @Index(name = "idx_score", columnList = "score"),
    @Index(name = "idx_assessed_at", columnList = "assessed_at")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SkillAssessment {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, length = 255)
    private String skill;

    @Column(nullable = false)
    private Integer score; // 0-100

    @Column(name = "assessed_at")
    private LocalDateTime assessedAt = LocalDateTime.now();

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id")
    private Session session;
}
