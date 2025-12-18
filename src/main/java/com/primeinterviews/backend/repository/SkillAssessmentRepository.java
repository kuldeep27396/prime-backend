package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.SkillAssessment;
import com.primeinterviews.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface SkillAssessmentRepository extends JpaRepository<SkillAssessment, UUID> {
    List<SkillAssessment> findByUser(User user);
    List<SkillAssessment> findByUserAndSkill(User user, String skill);
}
