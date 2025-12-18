package com.primeinterviews.backend.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "Standard success response")
public class SuccessResponse<T> {

    @Schema(description = "Success status", example = "true")
    @Builder.Default
    private Boolean success = true;

    @Schema(description = "Success message")
    private String message;

    @Schema(description = "Response data")
    private T data;
}
