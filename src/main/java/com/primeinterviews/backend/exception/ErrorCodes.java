package com.primeinterviews.backend.exception;

public class ErrorCodes {
    public static final String UNAUTHORIZED = "UNAUTHORIZED";
    public static final String FORBIDDEN = "FORBIDDEN";
    public static final String VALIDATION_ERROR = "VALIDATION_ERROR";
    public static final String NOT_FOUND = "NOT_FOUND";
    public static final String CONFLICT = "CONFLICT";
    public static final String RATE_LIMITED = "RATE_LIMITED";
    public static final String INTERNAL_ERROR = "INTERNAL_ERROR";
    public static final String SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE";

    private ErrorCodes() {
        // Private constructor to prevent instantiation
    }
}
