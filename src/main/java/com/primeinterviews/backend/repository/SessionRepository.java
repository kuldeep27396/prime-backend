package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.Session;
import com.primeinterviews.backend.entity.User;
import com.primeinterviews.backend.entity.Mentor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface SessionRepository extends JpaRepository<Session, UUID> {
    List<Session> findByUser(User user);
    List<Session> findByMentor(Mentor mentor);
    List<Session> findByStatus(String status);
    Page<Session> findByUser(User user, Pageable pageable);
    Page<Session> findByMentor(Mentor mentor, Pageable pageable);

    @Query("SELECT s FROM Session s WHERE s.scheduledAt BETWEEN :startDate AND :endDate")
    List<Session> findSessionsBetweenDates(LocalDateTime startDate, LocalDateTime endDate);

    List<Session> findByUserAndStatus(User user, String status);
    List<Session> findByMentorAndStatus(Mentor mentor, String status);
}
