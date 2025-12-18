package com.primeinterviews.backend.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.Components;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Value("${app.name}")
    private String appName;

    @Value("${app.version}")
    private String appVersion;

    @Bean
    public OpenAPI customOpenAPI() {
        final String securitySchemeName = "bearerAuth";

        return new OpenAPI()
                .info(new Info()
                        .title(appName)
                        .version(appVersion)
                        .description("""
                            **Prime Interviews API** - A comprehensive backend service for interview scheduling and management.

                            ## Features

                            * **User Management**: Create and manage user profiles with Clerk authentication
                            * **Mentor Discovery**: Search and filter mentors by skills, experience, and availability
                            * **Session Booking**: Schedule, manage, and track interview sessions
                            * **Video Integration**: Create and manage video call rooms for remote interviews
                            * **Analytics**: Comprehensive dashboard analytics and progress tracking
                            * **Email Notifications**: Automated email notifications for bookings and updates

                            ## Authentication

                            This API uses Clerk.js for authentication. Include your Clerk JWT token in the Authorization header:
                            ```
                            Authorization: Bearer <your_clerk_jwt_token>
                            ```

                            ## Rate Limiting

                            API endpoints are rate limited to ensure fair usage:
                            - General API: 100 requests per minute
                            - Email API: 10 requests per minute
                            - Search API: 30 requests per minute
                            """)
                        .contact(new Contact()
                                .name("Prime Interviews Team")
                                .email("support@prime-interviews.com"))
                        .license(new License()
                                .name("MIT License")
                                .url("https://opensource.org/licenses/MIT")))
                .addSecurityItem(new SecurityRequirement().addList(securitySchemeName))
                .components(new Components()
                        .addSecuritySchemes(securitySchemeName, new SecurityScheme()
                                .name(securitySchemeName)
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("Enter Clerk JWT token")));
    }
}
