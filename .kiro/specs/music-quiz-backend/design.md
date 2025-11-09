# Design Document: Music Quiz Backend

## Overview

The Music Quiz Backend is a serverless application built on AWS Lambda and API Gateway, deployed using AWS CDK with Python. The architecture follows a microservices pattern where each API endpoint is handled by a dedicated Lambda function. The system supports admin operations (authentication, quiz session management, audio upload) and participant operations (registration, quiz participation).

The backend integrates with a Vue/Vuetify frontend hosted on S3 via CloudFront at the domain katrin-goes-50.kornis.bayern, with comprehensive CORS configuration to enable cross-origin requests.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFront Distribution                   │
│              (katrin-goes-50.kornis.bayern)                 │
│                  ACM Certificate Attached                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTPS
                     │
┌────────────────────┴────────────────────────────────────────┐
│                      API Gateway (REST)                      │
│                    CORS Enabled on All Routes                │
└─────┬────────┬────────┬────────┬────────┬──────────┬────────┘
      │        │        │        │        │          │
      │        │        │        │        │          │
┌─────▼──┐ ┌──▼────┐ ┌─▼─────┐ ┌▼─────┐ ┌▼────────┐ ┌▼───────┐
│ Admin  │ │ Create│ │ Upload│ │ Get  │ │Register │ │  Get   │
│ Login  │ │ Quiz  │ │ Audio │ │ Quiz │ │Participant│ │ Audio │
│ Lambda │ │Lambda │ │Lambda │ │Lambda│ │ Lambda  │ │ Lambda │
└────┬───┘ └───┬───┘ └───┬───┘ └──┬───┘ └────┬────┘ └───┬────┘
     │         │         │        │          │          │
     └─────────┴─────────┴────────┴──────────┴──────────┘
                              │
                    ┌─────────▼──────────┐
                    │    DynamoDB Tables │
                    │  - Admins          │
                    │  - QuizSessions    │
                    │  - QuizRounds      │
                    │  - Participants    │
                    └────────────────────┘
                              
                    ┌────────────────────┐
                    │    S3 Bucket       │
                    │  Audio Files       │
                    └────────────────────┘
```

### Technology Stack

- **Runtime**: Python 3.11
- **Infrastructure**: AWS CDK (Python)
- **Compute**: AWS Lambda (individual functions per endpoint)
- **API**: API Gateway REST API
- **Storage**: DynamoDB for metadata, S3 for audio files
- **Authentication**: Custom JWT-based authentication
- **CORS**: Configured at API Gateway and Lambda response level

## Components and Interfaces

### 1. CDK Infrastructure Stack

**Purpose**: Define and deploy all AWS resources

**Key Components**:
- `MusicQuizStack`: Main CDK stack class
- Lambda function definitions (one per endpoint)
- API Gateway REST API with resource/method configurations
- DynamoDB table definitions
- S3 bucket for audio storage
- IAM roles and policies

**CDK Structure**:
```
cdk/
├── app.py                    # CDK app entry point
├── requirements.txt          # CDK dependencies
└── music_quiz_stack/
    ├── __init__.py
    ├── stack.py              # Main stack definition
    ├── lambda_functions.py   # Lambda construct definitions
    ├── api_gateway.py        # API Gateway configuration
    ├── database.py           # DynamoDB table definitions
    └── storage.py            # S3 bucket configuration
```

### 2. Lambda Functions

Each Lambda function is self-contained with no framework dependencies.

#### Admin Login Lambda
- **Path**: `POST /admin/login`
- **Input**: `{ "username": string, "password": string }`
- **Output**: `{ "token": string, "expiresIn": number }`
- **Logic**: Validate credentials against DynamoDB, generate JWT token

#### Create Quiz Session Lambda
- **Path**: `POST /admin/quiz-sessions`
- **Headers**: `Authorization: Bearer <token>`
- **Input**: `{ "title": string, "description": string }`
- **Output**: `{ "sessionId": string, "title": string, "createdAt": timestamp }`
- **Logic**: Validate admin token, create session in DynamoDB

#### Add Quiz Round Lambda
- **Path**: `POST /admin/quiz-sessions/{sessionId}/rounds`
- **Headers**: `Authorization: Bearer <token>`
- **Input**: `{ "audioKey": string, "answers": [string, string, string, string], "correctAnswer": number }`
- **Output**: `{ "roundId": string, "sessionId": string }`
- **Logic**: Validate admin token, validate session exists, add round (max 30 check)

#### Upload Audio Lambda
- **Path**: `POST /admin/audio`
- **Headers**: `Authorization: Bearer <token>`, `Content-Type: audio/*`
- **Input**: Binary audio data
- **Output**: `{ "audioKey": string, "url": string }`
- **Logic**: Validate admin token, generate unique key, upload to S3, return presigned URL

#### Get Quiz Session Lambda
- **Path**: `GET /quiz-sessions/{sessionId}`
- **Output**: `{ "sessionId": string, "title": string, "rounds": [...] }`
- **Logic**: Retrieve session and rounds from DynamoDB

#### List Quiz Sessions Lambda
- **Path**: `GET /quiz-sessions`
- **Output**: `{ "sessions": [{sessionId, title, createdAt}] }`
- **Logic**: Query all sessions from DynamoDB

#### Register Participant Lambda
- **Path**: `POST /participants/register`
- **Input**: `{ "name": string, "sessionId": string }`
- **Output**: `{ "participantId": string, "token": string }`
- **Logic**: Create participant record, generate participant token

#### Get Audio Lambda
- **Path**: `GET /audio/{audioKey}`
- **Output**: Presigned S3 URL redirect or audio stream
- **Logic**: Generate presigned URL for S3 object

#### Generate QR Code Data Lambda
- **Path**: `GET /quiz-sessions/{sessionId}/qr`
- **Output**: `{ "registrationUrl": string }`
- **Logic**: Return registration URL for QR code generation

### 3. CORS Configuration

**Implementation Strategy**: Two-layer CORS handling

**Layer 1: API Gateway CORS**
- Enable CORS on API Gateway resources
- Configure OPTIONS method for preflight requests
- Set response headers:
  - `Access-Control-Allow-Origin: *` (or specific CloudFront domain)
  - `Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS`
  - `Access-Control-Allow-Headers: Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token`

**Layer 2: Lambda Response Headers**
- Every Lambda function returns CORS headers in response
- Consistent header injection via shared utility function

**Shared CORS Utility** (`lambda_common/cors.py`):
```python
def add_cors_headers(response):
    response['headers'] = response.get('headers', {})
    response['headers'].update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    })
    return response
```

### 4. Authentication System

**Admin Authentication**:
- Admins stored in DynamoDB with hashed passwords (bcrypt)
- JWT tokens issued on successful login
- Token validation middleware in protected Lambda functions

**Participant Authentication**:
- Lightweight token generation on registration
- Token used to associate quiz responses with participants

**JWT Structure**:
```json
{
  "sub": "user_id",
  "role": "admin|participant",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Shared Auth Utility** (`lambda_common/auth.py`):
- `generate_token(user_id, role)`: Create JWT
- `validate_token(token)`: Verify and decode JWT
- `hash_password(password)`: Hash password with bcrypt
- `verify_password(password, hash)`: Verify password

## Data Models

### DynamoDB Tables

#### Admins Table
- **Table Name**: `MusicQuiz-Admins`
- **Primary Key**: `adminId` (String)
- **Attributes**:
  - `username` (String, GSI)
  - `passwordHash` (String)
  - `createdAt` (Number)

#### QuizSessions Table
- **Table Name**: `MusicQuiz-Sessions`
- **Primary Key**: `sessionId` (String)
- **Attributes**:
  - `title` (String)
  - `description` (String)
  - `createdBy` (String) - adminId
  - `createdAt` (Number)
  - `roundCount` (Number)
  - `status` (String) - "draft", "active", "completed"

#### QuizRounds Table
- **Table Name**: `MusicQuiz-Rounds`
- **Primary Key**: `roundId` (String)
- **Sort Key**: `sessionId` (String, GSI)
- **Attributes**:
  - `audioKey` (String) - S3 object key
  - `answers` (List) - [answer1, answer2, answer3, answer4]
  - `correctAnswer` (Number) - index 0-3
  - `roundNumber` (Number)
  - `createdAt` (Number)

#### Participants Table
- **Table Name**: `MusicQuiz-Participants`
- **Primary Key**: `participantId` (String)
- **Attributes**:
  - `name` (String)
  - `sessionId` (String, GSI)
  - `registeredAt` (Number)
  - `token` (String)

### S3 Bucket Structure

**Bucket Name**: `music-quiz-audio-{account-id}`

**Object Key Pattern**: `sessions/{sessionId}/audio/{uuid}.{extension}`

**Bucket Configuration**:
- Private access (no public read)
- Presigned URLs for audio access
- Lifecycle policy: Delete objects after 90 days
- CORS configuration to allow CloudFront origin

## Error Handling

### Error Response Format

All errors return consistent JSON structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., max rounds exceeded)
- `500 Internal Server Error`: Server-side error

### Error Handling Strategy

**Lambda Level**:
- Try-catch blocks around all operations
- Log errors to CloudWatch
- Return appropriate HTTP status with error details
- Always include CORS headers in error responses

**Common Error Scenarios**:
1. **Invalid Token**: Return 401 with CORS headers
2. **DynamoDB Error**: Return 500, log to CloudWatch
3. **S3 Upload Failure**: Return 500, cleanup partial data
4. **Max Rounds Exceeded**: Return 409 with clear message
5. **Invalid Audio Format**: Return 400 with supported formats

### Shared Error Utility (`lambda_common/errors.py`):
```python
def error_response(status_code, error_code, message, details=None):
    response = {
        'statusCode': status_code,
        'body': json.dumps({
            'error': {
                'code': error_code,
                'message': message,
                'details': details or {}
            }
        })
    }
    return add_cors_headers(response)
```

## Testing Strategy

### Unit Testing
- Test individual Lambda handler functions
- Mock AWS service calls (DynamoDB, S3)
- Test authentication utilities
- Test CORS header injection
- Framework: pytest with moto for AWS mocking

### Integration Testing
- Deploy to test AWS environment
- Test API Gateway → Lambda integration
- Test CORS with actual browser requests
- Test authentication flow end-to-end
- Verify S3 upload and presigned URL generation

### CORS Testing
- **Critical**: Test OPTIONS preflight requests
- Test actual requests from CloudFront domain
- Verify headers in both success and error responses
- Test with different HTTP methods (GET, POST)
- Use browser dev tools to verify CORS headers

### Load Testing
- Test concurrent Lambda invocations
- Verify DynamoDB throughput
- Test S3 upload with multiple files
- Validate 30 rounds per session limit

### Test Structure
```
tests/
├── unit/
│   ├── test_admin_login.py
│   ├── test_create_quiz.py
│   ├── test_upload_audio.py
│   └── test_auth_utils.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_cors.py
│   └── test_auth_flow.py
└── conftest.py  # Shared fixtures
```

## Deployment Strategy

### CDK Deployment Steps

1. **Bootstrap CDK** (one-time):
   ```bash
   cdk bootstrap aws://967169659906/us-east-1
   ```

2. **Install Dependencies**:
   ```bash
   cd cdk
   pip install -r requirements.txt
   ```

3. **Synthesize Stack**:
   ```bash
   cdk synth
   ```

4. **Deploy Stack**:
   ```bash
   cdk deploy
   ```

### Environment Configuration

**CDK Context** (`cdk.json`):
```json
{
  "app": "python3 app.py",
  "context": {
    "domain_name": "katrin-goes-50.kornis.bayern",
    "certificate_arn": "arn:aws:acm:us-east-1:967169659906:certificate/aa6370aa-fc9b-4d66-b106-9d11ceebb056",
    "aws_account": "967169659906",
    "aws_region": "us-east-1"
  }
}
```

### Lambda Deployment Package

Each Lambda function deployed with:
- Handler code
- Shared utilities (`lambda_common/`)
- Dependencies layer (if needed)

**Lambda Directory Structure**:
```
lambda/
├── admin_login/
│   └── handler.py
├── create_quiz/
│   └── handler.py
├── upload_audio/
│   └── handler.py
├── get_quiz/
│   └── handler.py
├── register_participant/
│   └── handler.py
├── get_audio/
│   └── handler.py
├── list_sessions/
│   └── handler.py
├── add_round/
│   └── handler.py
├── generate_qr/
│   └── handler.py
└── common/
    ├── __init__.py
    ├── cors.py
    ├── auth.py
    ├── errors.py
    └── db.py
```

## Security Considerations

1. **Authentication**: JWT tokens with expiration
2. **Password Storage**: bcrypt hashing with salt
3. **S3 Access**: Private bucket with presigned URLs
4. **API Gateway**: Rate limiting and throttling
5. **IAM**: Least privilege principle for Lambda roles
6. **Secrets**: Store JWT secret in AWS Secrets Manager
7. **Input Validation**: Validate all inputs in Lambda functions
8. **CORS**: Restrict to specific origin in production (CloudFront domain)

## API Endpoint Summary

| Method | Path                             | Lambda               | Auth  | Purpose                 |
| ------ | -------------------------------- | -------------------- | ----- | ----------------------- |
| POST   | /admin/login                     | admin_login          | No    | Admin authentication    |
| POST   | /admin/quiz-sessions             | create_quiz          | Admin | Create quiz session     |
| POST   | /admin/quiz-sessions/{id}/rounds | add_round            | Admin | Add quiz round          |
| POST   | /admin/audio                     | upload_audio         | Admin | Upload audio file       |
| GET    | /quiz-sessions                   | list_sessions        | No    | List all sessions       |
| GET    | /quiz-sessions/{id}              | get_quiz             | No    | Get session details     |
| GET    | /quiz-sessions/{id}/qr           | generate_qr          | No    | Get QR registration URL |
| POST   | /participants/register           | register_participant | No    | Register participant    |
| GET    | /audio/{key}                     | get_audio            | No    | Get audio file          |

## Future Considerations

- WebSocket support for real-time quiz participation
- CloudWatch dashboards for monitoring
- Backup strategy for DynamoDB tables
- Multi-region deployment for high availability
- Caching layer (CloudFront, API Gateway cache)
- Admin dashboard for analytics
