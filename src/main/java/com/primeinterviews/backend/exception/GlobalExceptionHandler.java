package com.primeinterviews.backend.exception;

import com.primeinterviews.backend.dto.ErrorDetail;
import com.primeinterviews.backend.dto.ErrorResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.AuthenticationCredentialsNotFoundException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFoundException(
            ResourceNotFoundException ex, WebRequest request) {
        log.error("Resource not found: {}", ex.getMessage());

        ErrorDetail errorDetail = ErrorDetail.builder()
                .code(ErrorCodes.NOT_FOUND)
                .message(ex.getMessage())
                .build();

        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .error(errorDetail)
                .build();

        return new ResponseEntity<>(errorResponse, HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(BadRequestException.class)
    public ResponseEntity<ErrorResponse> handleBadRequestException(
            BadRequestException ex, WebRequest request) {
        log.error("Bad request: {}", ex.getMessage());

        ErrorDetail errorDetail = ErrorDetail.builder()
                .code(ErrorCodes.VALIDATION_ERROR)
                .message(ex.getMessage())
                .build();

        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .error(errorDetail)
                .build();

        return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(UnauthorizedException.class)
    public ResponseEntity<ErrorResponse> handleUnauthorizedException(
            UnauthorizedException ex, WebRequest request) {
        log.error("Unauthorized: {}", ex.getMessage());

        ErrorDetail errorDetail = ErrorDetail.builder()
                .code(ErrorCodes.UNAUTHORIZED)
                .message(ex.getMessage())
                .build();

        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .error(errorDetail)
                .build();

        return new ResponseEntity<>(errorResponse, HttpStatus.UNAUTHORIZED);
    }

    @ExceptionHandler({AccessDeniedException.class, AuthenticationCredentialsNotFoundException.class})
    public ResponseEntity<ErrorResponse> handleAccessDeniedException(
            Exception ex, WebRequest request) {
        log.error("Access denied: {}", ex.getMessage());

        ErrorDetail errorDetail = ErrorDetail.builder()
                .code(ErrorCodes.FORBIDDEN)
                .message("Access denied")
                .build();

        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .error(errorDetail)
                .build();

        return new ResponseEntity<>(errorResponse, HttpStatus.FORBIDDEN);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex, WebRequest request) {
        log.error("Validation error: {}", ex.getMessage());

        Map<String, Object> details = new HashMap<>();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {
            details.put(error.getField(), error.getDefaultMessage());
        }

        ErrorDetail errorDetail = ErrorDetail.builder()
                .code(ErrorCodes.VALIDATION_ERROR)
                .message("Request validation failed")
                .details(details)
                .build();

        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .error(errorDetail)
                .build();

        return new ResponseEntity<>(errorResponse, HttpStatus.UNPROCESSABLE_ENTITY);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ErrorResponse> handleHttpMessageNotReadable(
            HttpMessageNotReadableException ex, WebRequest request) {
        log.error("Malformed JSON request: {}", ex.getMessage());

        ErrorDetail errorDetail = ErrorDetail.builder()
                .code(ErrorCodes.VALIDATION_ERROR)
                .message("Malformed JSON request")
                .build();

        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .error(errorDetail)
                .build();

        return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGlobalException(
            Exception ex, WebRequest request) {
        log.error("Internal server error: ", ex);

        ErrorDetail errorDetail = ErrorDetail.builder()
                .code(ErrorCodes.INTERNAL_ERROR)
                .message("Internal server error occurred")
                .build();

        ErrorResponse errorResponse = ErrorResponse.builder()
                .success(false)
                .error(errorDetail)
                .build();

        return new ResponseEntity<>(errorResponse, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}
