package com.primeinterviews.backend.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "Error detail information")
public class ErrorDetail {

    @Schema(description = "Error code", example = "VALIDATION_ERROR")
    private String code;

    @Schema(description = "Error message", example = "Request validation failed")
    private String message;

    @Schema(description = "Additional error details")
    private Map<String, Object> details;
}
