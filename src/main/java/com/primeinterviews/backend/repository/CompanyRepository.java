package com.primeinterviews.backend.repository;

import com.primeinterviews.backend.entity.Company;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface CompanyRepository extends JpaRepository<Company, UUID> {
    Optional<Company> findByName(String name);
    List<Company> findByIsActiveTrue();
    List<Company> findByIndustry(String industry);
}
