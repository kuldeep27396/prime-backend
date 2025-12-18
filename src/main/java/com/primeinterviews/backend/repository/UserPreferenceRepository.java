package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.UserPreference;
import com.primeinterviews.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserPreferenceRepository extends JpaRepository<UserPreference, UUID> {
    Optional<UserPreference> findByUser(User user);
}
