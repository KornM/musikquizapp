# Requirements Document

## Introduction

This document specifies the requirements for a Music Quiz Application backend system. The system enables administrators to create and manage music quiz sessions with audio snippets and multiple-choice answers, while allowing participants to register and participate in quiz sessions via mobile devices. The backend is built on AWS Lambda with Python, deployed via AWS CDK, and exposed through API Gateway with proper CORS configuration for a CloudFront-hosted frontend.

## Glossary

- **Quiz System**: The complete backend infrastructure including Lambda functions, API Gateway, and data storage
- **Admin User**: An authenticated user with privileges to create and manage quiz sessions
- **Participant**: A registered user who can join and participate in quiz sessions
- **Quiz Session**: A collection of up to 30 quiz rounds prepared by an admin
- **Quiz Round**: A single question consisting of an audio snippet and 4 possible answers
- **API Gateway**: AWS REST API Gateway that routes HTTP requests to Lambda functions
- **Lambda Function**: Individual AWS Lambda function handling a specific API endpoint
- **CDK Stack**: AWS Cloud Development Kit infrastructure-as-code deployment
- **CORS**: Cross-Origin Resource Sharing configuration enabling frontend-backend communication
- **Audio Snippet**: A music file uploaded by admin for a quiz round
- **QR Code**: Quick Response code displayed for participant registration

## Requirements

### Requirement 1: User Authentication and Authorization

**User Story:** As a system administrator, I want secure authentication mechanisms so that only authorized users can access admin functions and participants can securely register.

#### Acceptance Criteria

1. THE Quiz System SHALL provide an authentication endpoint for admin login
2. THE Quiz System SHALL provide a registration endpoint for participant self-registration
3. WHEN an admin attempts to access protected endpoints, THE Quiz System SHALL validate admin credentials
4. WHEN a participant registers, THE Quiz System SHALL create a unique participant identity
5. THE Quiz System SHALL maintain separate authorization levels for admin and participant roles

### Requirement 2: Quiz Session Management

**User Story:** As an admin, I want to create and manage quiz sessions with multiple rounds so that I can prepare engaging music quizzes for participants.

#### Acceptance Criteria

1. THE Quiz System SHALL provide an endpoint to create a new quiz session
2. THE Quiz System SHALL support up to 30 quiz rounds per session
3. WHEN an admin uploads an audio snippet, THE Quiz System SHALL store the audio file securely
4. THE Quiz System SHALL provide an endpoint to add quiz rounds with 4 possible answers to a session
5. THE Quiz System SHALL provide an endpoint to retrieve quiz session details
6. THE Quiz System SHALL provide an endpoint to list all quiz sessions

### Requirement 3: Participant Registration

**User Story:** As a participant, I want to register for a quiz session using a QR code on my mobile device so that I can quickly join the quiz.

#### Acceptance Criteria

1. THE Quiz System SHALL provide an endpoint to generate registration data for QR code display
2. WHEN a participant scans a QR code, THE Quiz System SHALL accept registration requests from mobile devices
3. THE Quiz System SHALL provide an endpoint to register participants for a specific quiz session
4. THE Quiz System SHALL store participant information associated with quiz sessions

### Requirement 4: API Gateway Architecture

**User Story:** As a developer, I want each API endpoint handled by a separate Lambda function so that the system is modular and scalable.

#### Acceptance Criteria

1. THE Quiz System SHALL deploy a separate Lambda function for each API endpoint
2. THE Quiz System SHALL configure API Gateway with REST API routing to Lambda functions
3. THE Quiz System SHALL NOT use web frameworks within Lambda functions
4. WHEN API Gateway receives a request, THE Quiz System SHALL route it to the corresponding Lambda function
5. THE Quiz System SHALL implement Lambda functions using Python runtime

### Requirement 5: CORS Configuration

**User Story:** As a frontend developer, I want proper CORS headers configured so that the CloudFront-hosted frontend can communicate with the API without browser restrictions.

#### Acceptance Criteria

1. THE Quiz System SHALL configure CORS headers on all API Gateway endpoints
2. THE Quiz System SHALL include Access-Control-Allow-Origin header in all API responses
3. THE Quiz System SHALL include Access-Control-Allow-Methods header specifying allowed HTTP methods
4. THE Quiz System SHALL include Access-Control-Allow-Headers header for request headers
5. THE Quiz System SHALL handle OPTIONS preflight requests for CORS

### Requirement 6: Infrastructure Deployment

**User Story:** As a DevOps engineer, I want the entire infrastructure defined in AWS CDK using Python so that deployment is automated and reproducible.

#### Acceptance Criteria

1. THE Quiz System SHALL define all infrastructure using AWS CDK with Python
2. THE Quiz System SHALL deploy Lambda functions through CDK Stack
3. THE Quiz System SHALL configure API Gateway through CDK Stack
4. THE Quiz System SHALL configure IAM roles and permissions through CDK Stack
5. WHEN CDK deployment executes, THE Quiz System SHALL create all required AWS resources

### Requirement 7: CloudFront Integration

**User Story:** As a system architect, I want the API to work seamlessly with a CloudFront-hosted frontend so that users have a unified experience.

#### Acceptance Criteria

1. THE Quiz System SHALL configure API Gateway to accept requests from CloudFront distribution
2. THE Quiz System SHALL support the alternate domain name katrin-goes-50.kornis.bayern
3. THE Quiz System SHALL integrate with existing ACM certificate arn:aws:acm:us-east-1:967169659906:certificate/aa6370aa-fc9b-4d66-b106-9d11ceebb056
4. THE Quiz System SHALL configure CORS to allow requests from the CloudFront domain

### Requirement 8: Data Storage

**User Story:** As a backend developer, I want persistent storage for quiz sessions, rounds, and user data so that information is retained across Lambda invocations.

#### Acceptance Criteria

1. THE Quiz System SHALL provide persistent storage for quiz session data
2. THE Quiz System SHALL provide persistent storage for quiz round data including audio snippets
3. THE Quiz System SHALL provide persistent storage for admin credentials
4. THE Quiz System SHALL provide persistent storage for participant registrations
5. WHEN a Lambda function stores data, THE Quiz System SHALL ensure data persistence across invocations

### Requirement 9: Audio File Management

**User Story:** As an admin, I want to upload audio snippets for quiz rounds so that participants can hear music during the quiz.

#### Acceptance Criteria

1. THE Quiz System SHALL provide an endpoint to upload audio files
2. THE Quiz System SHALL store audio files in a secure storage service
3. THE Quiz System SHALL support common audio formats (MP3, WAV, M4A)
4. THE Quiz System SHALL provide an endpoint to retrieve audio files for playback
5. WHEN an audio file is uploaded, THE Quiz System SHALL associate it with the corresponding quiz round

### Requirement 10: API Response Format

**User Story:** As a frontend developer, I want consistent JSON response formats from all API endpoints so that I can reliably parse responses.

#### Acceptance Criteria

1. THE Quiz System SHALL return responses in JSON format
2. THE Quiz System SHALL include appropriate HTTP status codes in responses
3. WHEN an error occurs, THE Quiz System SHALL return error details in JSON format
4. THE Quiz System SHALL include CORS headers in all responses including error responses
5. THE Quiz System SHALL use consistent field naming conventions across all endpoints
