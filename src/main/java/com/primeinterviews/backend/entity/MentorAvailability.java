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
@Table(name = "mentor_availability", indexes = {
    @Index(name = "idx_ma_mentor_id", columnList = "mentor_id"),
    @Index(name = "idx_day_of_week", columnList = "day_of_week"),
    @Index(name = "idx_is_available", columnList = "is_available"),
    @Index(name = "idx_recurring", columnList = "recurring"),
    @Index(name = "idx_ma_created_at", columnList = "created_at"),
    @Index(name = "idx_ma_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class MentorAvailability {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "mentor_id", nullable = false)
    private Mentor mentor;

    @Column(name = "day_of_week", nullable = false)
    private Integer dayOfWeek; // 0-6 (Sunday-Saturday)

    @Column(name = "start_time", nullable = false, length = 5)
    private String startTime; // HH:MM format

    @Column(name = "end_time", nullable = false, length = 5)
    private String endTime; // HH:MM format

    @Column(nullable = false, length = 100)
    private String timezone;

    @Column(name = "is_available")
    private Boolean isAvailable = true;

    private Boolean recurring = true;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
