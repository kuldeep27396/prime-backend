package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "company_mentors", indexes = {
    @Index(name = "idx_cm_company_id", columnList = "company_id"),
    @Index(name = "idx_cm_mentor_id", columnList = "mentor_id"),
    @Index(name = "idx_is_current", columnList = "is_current")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CompanyMentor {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "company_id", nullable = false)
    private Company company;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "mentor_id", nullable = false)
    private Mentor mentor;

    @Column(length = 255)
    private String position;

    @Column(name = "start_date")
    private LocalDateTime startDate;

    @Column(name = "end_date")
    private LocalDateTime endDate;

    @Column(name = "is_current")
    private Boolean isCurrent = true;
}
