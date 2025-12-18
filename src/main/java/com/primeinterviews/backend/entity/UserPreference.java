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
@Table(name = "user_preferences", indexes = {
    @Index(name = "idx_pref_user_id", columnList = "user_id"),
    @Index(name = "idx_pref_created_at", columnList = "created_at"),
    @Index(name = "idx_pref_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserPreference {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "recent_searches", columnDefinition = "jsonb")
    private String recentSearches; // JSON array

    @Column(name = "favorite_topics", columnDefinition = "jsonb")
    private String favoriteTopics; // JSON array

    @Column(name = "favorite_mentors", columnDefinition = "jsonb")
    private String favoriteMentors; // JSON array

    @Column(length = 100)
    private String timezone;

    @Column(name = "notification_settings", columnDefinition = "jsonb")
    private String notificationSettings; // JSON object

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
