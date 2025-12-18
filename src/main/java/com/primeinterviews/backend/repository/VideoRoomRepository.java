package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.VideoRoom;
import com.primeinterviews.backend.entity.Session;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface VideoRoomRepository extends JpaRepository<VideoRoom, UUID> {
    Optional<VideoRoom> findByRoomId(String roomId);
    List<VideoRoom> findBySession(Session session);
    List<VideoRoom> findByStatus(String status);
}
