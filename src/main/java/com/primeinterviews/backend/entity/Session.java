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
@Table(name = "sessions", indexes = {
    @Index(name = "idx_session_user_id", columnList = "user_id"),
    @Index(name = "idx_session_mentor_id", columnList = "mentor_id"),
    @Index(name = "idx_session_type", columnList = "session_type"),
    @Index(name = "idx_scheduled_at", columnList = "scheduled_at"),
    @Index(name = "idx_duration", columnList = "duration"),
    @Index(name = "idx_meeting_type", columnList = "meeting_type"),
    @Index(name = "idx_status", columnList = "status"),
    @Index(name = "idx_session_created_at", columnList = "created_at"),
    @Index(name = "idx_session_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Session {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "mentor_id", nullable = false)
    private Mentor mentor;

    @Column(name = "session_type", nullable = false, length = 255)
    private String sessionType;

    @Column(name = "scheduled_at", nullable = false)
    private LocalDateTime scheduledAt;

    @Column(nullable = false)
    private Integer duration; // Duration in minutes

    @Column(name = "meeting_type", length = 50)
    private String meetingType; // video, audio, in-person

    @Column(name = "meeting_link", columnDefinition = "TEXT")
    private String meetingLink;

    @Column(length = 50)
    private String status = "pending"; // pending, confirmed, completed, cancelled

    @Column(name = "record_session")
    private Boolean recordSession = false;

    @Column(name = "special_requests", columnDefinition = "TEXT")
    private String specialRequests;

    private Integer rating; // 1-5

    @Column(columnDefinition = "TEXT")
    private String feedback;

    @Column(name = "cancellation_reason", columnDefinition = "TEXT")
    private String cancellationReason;

    @Column(name = "recording_url", columnDefinition = "TEXT")
    private String recordingUrl;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "session", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Review> reviews;

    @OneToMany(mappedBy = "session", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<VideoRoom> videoRooms;
}
