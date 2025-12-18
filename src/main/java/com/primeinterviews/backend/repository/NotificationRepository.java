package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.Notification;
import com.primeinterviews.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface NotificationRepository extends JpaRepository<Notification, UUID> {
    List<Notification> findByUser(User user);
    List<Notification> findByUserAndIsReadFalse(User user);
    List<Notification> findByType(String type);
}
