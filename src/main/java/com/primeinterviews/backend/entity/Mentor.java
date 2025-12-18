package com.primeinterviews.backend.entity;

import com.vladmihalcea.hibernate.type.json.JsonBinaryType;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Type;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "mentors", indexes = {
    @Index(name = "idx_mentor_user_id", columnList = "user_id"),
    @Index(name = "idx_mentor_name", columnList = "name"),
    @Index(name = "idx_current_company", columnList = "current_company"),
    @Index(name = "idx_experience", columnList = "experience"),
    @Index(name = "idx_rating", columnList = "rating"),
    @Index(name = "idx_review_count", columnList = "review_count"),
    @Index(name = "idx_is_active", columnList = "is_active"),
    @Index(name = "idx_mentor_created_at", columnList = "created_at"),
    @Index(name = "idx_mentor_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Mentor {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, length = 255)
    private String name;

    @Column(length = 255)
    private String title;

    @Column(name = "current_company", length = 255)
    private String currentCompany;

    @Column(name = "previous_companies", columnDefinition = "jsonb")
    private String previousCompanies; // JSON array

    @Column(columnDefinition = "TEXT")
    private String avatar;

    @Column(columnDefinition = "TEXT")
    private String bio;

    @Column(columnDefinition = "jsonb")
    private String specialties; // JSON array

    @Column(columnDefinition = "jsonb")
    private String skills; // JSON array

    @Column(columnDefinition = "jsonb")
    private String languages; // JSON array

    private Integer experience;

    @Column(precision = 3, scale = 2)
    private BigDecimal rating = BigDecimal.ZERO;

    @Column(name = "review_count")
    private Integer reviewCount = 0;

    @Column(name = "hourly_rate", precision = 8, scale = 2)
    private BigDecimal hourlyRate;

    @Column(name = "response_time", length = 50)
    private String responseTime;

    @Column(length = 100)
    private String timezone;

    @Column(columnDefinition = "jsonb")
    private String availability; // JSON array

    @Column(name = "is_active")
    private Boolean isActive = true;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "mentor", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Session> sessions;

    @OneToMany(mappedBy = "mentor", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Review> reviews;
}
