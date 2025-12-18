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
@Table(name = "user_profiles", indexes = {
    @Index(name = "idx_profile_user_id", columnList = "user_id"),
    @Index(name = "idx_profile_created_at", columnList = "created_at"),
    @Index(name = "idx_profile_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserProfile {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "target_companies", columnDefinition = "jsonb")
    private String targetCompanies; // JSON array

    @Column(name = "focus_areas", columnDefinition = "jsonb")
    private String focusAreas; // JSON array

    @Column(name = "preferred_interview_types", columnDefinition = "jsonb")
    private String preferredInterviewTypes; // JSON array

    @Column(name = "years_of_experience")
    private Integer yearsOfExperience;

    @Column(name = "current_role", length = 255)
    private String currentRole;

    @Column(name = "current_company", length = 255)
    private String currentCompany;

    @Column(length = 255)
    private String location;

    @Column(name = "linkedin_url", columnDefinition = "TEXT")
    private String linkedinUrl;

    @Column(name = "github_url", columnDefinition = "TEXT")
    private String githubUrl;

    @Column(name = "portfolio_url", columnDefinition = "TEXT")
    private String portfolioUrl;

    @Column(name = "resume_url", columnDefinition = "TEXT")
    private String resumeUrl;

    @Column(columnDefinition = "TEXT")
    private String bio;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
