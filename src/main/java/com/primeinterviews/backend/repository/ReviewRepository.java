package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.Review;
import com.primeinterviews.backend.entity.Mentor;
import com.primeinterviews.backend.entity.User;
import com.primeinterviews.backend.entity.Session;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ReviewRepository extends JpaRepository<Review, UUID> {
    List<Review> findByMentor(Mentor mentor);
    List<Review> findByUser(User user);
    List<Review> findBySession(Session session);
    Page<Review> findByMentorAndIsPublicTrue(Mentor mentor, Pageable pageable);
    List<Review> findByIsPublicTrue();
}
