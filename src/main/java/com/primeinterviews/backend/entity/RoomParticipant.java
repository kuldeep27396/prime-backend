package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "room_participants", indexes = {
    @Index(name = "idx_participant_room_id", columnList = "room_id"),
    @Index(name = "idx_participant_user_id", columnList = "user_id"),
    @Index(name = "idx_participant_type", columnList = "participant_type"),
    @Index(name = "idx_joined_at", columnList = "joined_at"),
    @Index(name = "idx_participant_active", columnList = "is_active")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RoomParticipant {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "room_id", nullable = false)
    private VideoRoom videoRoom;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "participant_type", nullable = false, length = 50)
    private String participantType; // participant, mentor, observer

    @Column(name = "joined_at")
    private LocalDateTime joinedAt = LocalDateTime.now();

    @Column(name = "left_at")
    private LocalDateTime leftAt;

    @Column(name = "is_active")
    private Boolean isActive = true;
}
