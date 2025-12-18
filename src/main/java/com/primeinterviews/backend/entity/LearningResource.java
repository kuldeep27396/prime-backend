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
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "learning_resources", indexes = {
    @Index(name = "idx_resource_title", columnList = "title"),
    @Index(name = "idx_content_type", columnList = "content_type"),
    @Index(name = "idx_difficulty_level", columnList = "difficulty_level"),
    @Index(name = "idx_is_premium", columnList = "is_premium"),
    @Index(name = "idx_resource_created_at", columnList = "created_at"),
    @Index(name = "idx_resource_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LearningResource {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @Column(nullable = false, length = 255)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "content_type", nullable = false, length = 100)
    private String contentType; // article, video, course, book

    @Column(columnDefinition = "TEXT")
    private String url;

    @Column(name = "thumbnail_url", columnDefinition = "TEXT")
    private String thumbnailUrl;

    @Column(name = "difficulty_level", length = 50)
    private String difficultyLevel; // beginner, intermediate, advanced

    @Column(name = "duration_minutes")
    private Integer durationMinutes;

    @Column(name = "skills_covered", columnDefinition = "jsonb")
    private String skillsCovered; // JSON array

    @Column(columnDefinition = "jsonb")
    private String tags; // JSON array

    @Column(name = "is_premium")
    private Boolean isPremium = false;

    @Column(name = "view_count")
    private Integer viewCount = 0;

    @Column(precision = 3, scale = 2)
    private BigDecimal rating = BigDecimal.ZERO;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "resource", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<UserProgress> userProgress;
}
