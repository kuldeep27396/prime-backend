package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.Mentor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface MentorRepository extends JpaRepository<Mentor, UUID> {
    List<Mentor> findByIsActiveTrue();
    Page<Mentor> findByIsActiveTrue(Pageable pageable);

    @Query("SELECT m FROM Mentor m WHERE m.isActive = true AND " +
           "(:name IS NULL OR LOWER(m.name) LIKE LOWER(CONCAT('%', :name, '%')))")
    Page<Mentor> searchMentors(@Param("name") String name, Pageable pageable);

    List<Mentor> findByCurrentCompany(String company);
}
