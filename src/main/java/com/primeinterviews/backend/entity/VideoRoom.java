package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "video_rooms", indexes = {
    @Index(name = "idx_room_id", columnList = "room_id"),
    @Index(name = "idx_video_session_id", columnList = "session_id"),
    @Index(name = "idx_room_status", columnList = "status"),
    @Index(name = "idx_video_created_at", columnList = "created_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class VideoRoom {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @Column(name = "room_id", unique = true, nullable = false, length = 255)
    private String roomId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private Session session;

    @Column(name = "room_url", nullable = false, columnDefinition = "TEXT")
    private String roomUrl;

    @Column(name = "participant_token", columnDefinition = "TEXT")
    private String participantToken;

    @Column(name = "mentor_token", columnDefinition = "TEXT")
    private String mentorToken;

    @Column(length = 50)
    private String status = "active"; // active, ended

    @Column(name = "recording_url", columnDefinition = "TEXT")
    private String recordingUrl;

    @Column(name = "actual_duration")
    private Integer actualDuration; // Actual duration in minutes

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "ended_at")
    private LocalDateTime endedAt;

    // Relationships
    @OneToMany(mappedBy = "videoRoom", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<RoomParticipant> participants;
}
