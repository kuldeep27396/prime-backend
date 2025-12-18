package com.primeinterviews.backend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "email_templates", indexes = {
    @Index(name = "idx_template_name_unique", columnList = "name"),
    @Index(name = "idx_template_type", columnList = "template_type"),
    @Index(name = "idx_template_active", columnList = "is_active"),
    @Index(name = "idx_email_template_created_at", columnList = "created_at"),
    @Index(name = "idx_email_template_updated_at", columnList = "updated_at")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class EmailTemplate {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;

    @Column(nullable = false, unique = true, length = 255)
    private String name;

    @Column(nullable = false, length = 255)
    private String subject;

    @Column(name = "html_content", nullable = false, columnDefinition = "TEXT")
    private String htmlContent;

    @Column(name = "text_content", columnDefinition = "TEXT")
    private String textContent;

    @Column(name = "template_type", nullable = false, length = 100)
    private String templateType; // session_booking, reminder, review_request

    @Column(name = "is_active")
    private Boolean isActive = true;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
