package com.primeinterviews.backend.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Standard error response")
public class ErrorResponse {

    @Schema(description = "Success status", example = "false")
    @Builder.Default
    private Boolean success = false;

    @Schema(description = "Error details")
    private ErrorDetail error;
}
