# Music Quiz API Documentation

Base URL: `https://YOUR_API_GATEWAY_ID.execute-api.eu-central-1.amazonaws.com/prod`

## Table of Contents

- [Authentication](#authentication)
- [Super Admin Endpoints](#super-admin-endpoints)
- [Tenant Admin Endpoints](#tenant-admin-endpoints)
- [Participant Endpoints](#participant-endpoints)
- [Public Endpoints](#public-endpoints)
- [Error Responses](#error-responses)
- [Data Models](#data-models)

## Authentication

### Overview

The API supports three types of authentication:

1. **Super Admin**: Full system access, can manage tenants and tenant admins
2. **Tenant Admin**: Access to manage quiz sessions within their tenant
3. **Participant**: Access to join sessions and submit answers within their tenant

### Admin Authentication

Admin endpoints require a JWT token obtained through the login endpoint. Include the token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

**Token Payload (Admin):**
```json
{
  "adminId": "uuid",
  "tenantId": "uuid",
  "role": "super_admin" | "tenant_admin",
  "exp": 1234567890
}
```

### Participant Authentication

Participant endpoints require a JWT token obtained through registration. Include the token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

**Token Payload (Participant):**
```json
{
  "participantId": "uuid",
  "tenantId": "uuid",
  "exp": 1234567890
}
```

All tokens expire after 24 hours.

---

## Super Admin Endpoints

### 1. Create Tenant

Create a new tenant organization.

**Endpoint:** `POST /super-admin/tenants`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "description": "Corporate quiz events"
}
```

**Success Response (201):**
```json
{
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corporation",
  "description": "Corporate quiz events",
  "status": "active",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body or missing name
- `401` - Missing or invalid token
- `403` - Insufficient permissions (not super admin)

**Example:**
```bash
curl -X POST https://YOUR_API/super-admin/tenants \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Corporation","description":"Corporate quiz events"}'
```

---

### 2. List Tenants

Get a list of all tenants.

**Endpoint:** `GET /super-admin/tenants`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
```

**Query Parameters:**
- `status` (optional) - Filter by status: `active` or `inactive`

**Success Response (200):**
```json
{
  "tenants": [
    {
      "tenantId": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Acme Corporation",
      "description": "Corporate quiz events",
      "status": "active",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    },
    {
      "tenantId": "660e8400-e29b-41d4-a716-446655440001",
      "name": "University Quiz Club",
      "description": "Student quiz competitions",
      "status": "active",
      "createdAt": "2024-01-10T14:20:00Z",
      "updatedAt": "2024-01-10T14:20:00Z"
    }
  ]
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Insufficient permissions

**Example:**
```bash
curl https://YOUR_API/super-admin/tenants \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN"
```

---

### 3. Update Tenant

Update tenant information.

**Endpoint:** `PUT /super-admin/tenants/{tenantId}`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `tenantId` - UUID of the tenant

**Request Body:**
```json
{
  "name": "Acme Corp Updated",
  "description": "Updated description",
  "status": "active"
}
```

**Success Response (200):**
```json
{
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corp Updated",
  "description": "Updated description",
  "status": "active",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-20T15:45:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Tenant not found

---

### 4. Delete Tenant

Soft delete a tenant (marks as inactive).

**Endpoint:** `DELETE /super-admin/tenants/{tenantId}`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
```

**Path Parameters:**
- `tenantId` - UUID of the tenant

**Success Response (200):**
```json
{
  "message": "Tenant deleted successfully",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Tenant not found

---

### 5. Create Tenant Admin

Create an admin user for a specific tenant.

**Endpoint:** `POST /super-admin/tenants/{tenantId}/admins`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `tenantId` - UUID of the tenant

**Request Body:**
```json
{
  "username": "admin_acme",
  "password": "SecurePassword123!",
  "email": "admin@acme.com"
}
```

**Success Response (201):**
```json
{
  "adminId": "770e8400-e29b-41d4-a716-446655440002",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin_acme",
  "email": "admin@acme.com",
  "role": "tenant_admin",
  "createdAt": "2024-01-15T11:00:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body or missing fields
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Tenant not found
- `409` - Username already exists

---

### 6. List Tenant Admins

Get all admins for a specific tenant.

**Endpoint:** `GET /super-admin/tenants/{tenantId}/admins`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
```

**Path Parameters:**
- `tenantId` - UUID of the tenant

**Success Response (200):**
```json
{
  "admins": [
    {
      "adminId": "770e8400-e29b-41d4-a716-446655440002",
      "tenantId": "550e8400-e29b-41d4-a716-446655440000",
      "username": "admin_acme",
      "email": "admin@acme.com",
      "role": "tenant_admin",
      "createdAt": "2024-01-15T11:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Tenant not found

---

### 7. Update Tenant Admin

Update admin information.

**Endpoint:** `PUT /super-admin/admins/{adminId}`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `adminId` - UUID of the admin

**Request Body:**
```json
{
  "username": "admin_acme_updated",
  "email": "newemail@acme.com",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Success Response (200):**
```json
{
  "adminId": "770e8400-e29b-41d4-a716-446655440002",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin_acme_updated",
  "email": "newemail@acme.com",
  "role": "tenant_admin",
  "updatedAt": "2024-01-20T16:00:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Admin not found

---

### 8. Delete Tenant Admin

Delete an admin user.

**Endpoint:** `DELETE /super-admin/admins/{adminId}`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
```

**Path Parameters:**
- `adminId` - UUID of the admin

**Success Response (200):**
```json
{
  "message": "Admin deleted successfully",
  "adminId": "770e8400-e29b-41d4-a716-446655440002"
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Admin not found

---

### 9. Reset Admin Password

Reset an admin's password.

**Endpoint:** `POST /super-admin/admins/{adminId}/reset-password`

**Headers:**
```
Authorization: Bearer <super_admin_jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `adminId` - UUID of the admin

**Request Body:**
```json
{
  "newPassword": "NewSecurePassword456!"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset successfully",
  "adminId": "770e8400-e29b-41d4-a716-446655440002"
}
```

**Error Responses:**
- `400` - Invalid request body or weak password
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Admin not found

---

## Tenant Admin Endpoints

### 10. Admin Login

Authenticate as an admin and receive a JWT token with tenant context.

**Endpoint:** `POST /admin/login`

**Request Body:**
```json
{
  "username": "admin_acme",
  "password": "SecurePassword123!"
}
```

**Success Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 86400,
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "role": "tenant_admin"
}
```

**Error Responses:**
- `400` - Invalid request body or missing fields
- `401` - Invalid credentials

**Example:**
```bash
curl -X POST https://YOUR_API/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_acme","password":"SecurePassword123!"}'
```

---

### 11. Create Quiz Session

Create a new quiz session (automatically associated with admin's tenant).

**Endpoint:** `POST /admin/sessions`

**Headers:**
```
Authorization: Bearer <tenant_admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "80s Music Quiz",
  "description": "Test your knowledge of 80s hits!"
}
```

**Success Response (201):**
```json
{
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "title": "80s Music Quiz",
  "description": "Test your knowledge of 80s hits!",
  "createdBy": "770e8400-e29b-41d4-a716-446655440002",
  "createdAt": "2024-01-20T10:00:00Z",
  "roundCount": 0,
  "status": "draft"
}
```

**Error Responses:**
- `400` - Invalid request body or tenant inactive
- `401` - Missing or invalid token
- `403` - Insufficient permissions

---

### 12. List Quiz Sessions

Get all quiz sessions for the admin's tenant.

**Endpoint:** `GET /admin/sessions`

**Headers:**
```
Authorization: Bearer <tenant_admin_jwt_token>
```

**Success Response (200):**
```json
{
  "sessions": [
    {
      "sessionId": "880e8400-e29b-41d4-a716-446655440003",
      "tenantId": "550e8400-e29b-41d4-a716-446655440000",
      "title": "80s Music Quiz",
      "description": "Test your knowledge of 80s hits!",
      "createdBy": "770e8400-e29b-41d4-a716-446655440002",
      "createdAt": "2024-01-20T10:00:00Z",
      "roundCount": 5,
      "status": "active"
    }
  ]
}
```

**Note:** Only returns sessions belonging to the admin's tenant.

---

### 13. Get Quiz Session

Get detailed information about a specific quiz session.

**Endpoint:** `GET /admin/sessions/{sessionId}`

**Headers:**
```
Authorization: Bearer <tenant_admin_jwt_token>
```

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Success Response (200):**
```json
{
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "title": "80s Music Quiz",
  "description": "Test your knowledge of 80s hits!",
  "createdBy": "770e8400-e29b-41d4-a716-446655440002",
  "createdAt": "2024-01-20T10:00:00Z",
  "roundCount": 2,
  "status": "active",
  "rounds": [...]
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Cross-tenant access denied
- `404` - Session not found

---

### 14. Get Session Participants

Get all participants who have joined a session.

**Endpoint:** `GET /admin/sessions/{sessionId}/participants`

**Headers:**
```
Authorization: Bearer <tenant_admin_jwt_token>
```

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Success Response (200):**
```json
{
  "participants": [
    {
      "participantId": "990e8400-e29b-41d4-a716-446655440004",
      "participationId": "aa0e8400-e29b-41d4-a716-446655440005",
      "name": "John Doe",
      "avatar": "😀",
      "totalPoints": 150,
      "correctAnswers": 5,
      "joinedAt": "2024-01-20T11:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Cross-tenant access denied
- `404` - Session not found

---

## Participant Endpoints

### 15. Register Global Participant

Register a new global participant for a tenant.

**Endpoint:** `POST /participants/register`

**Request Body:**
```json
{
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "avatar": "😀"
}
```

**Success Response (201):**
```json
{
  "participantId": "990e8400-e29b-41d4-a716-446655440004",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "avatar": "😀",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "createdAt": "2024-01-20T11:00:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body or missing fields
- `404` - Tenant not found or inactive

**Example:**
```bash
curl -X POST https://YOUR_API/participants/register \
  -H "Content-Type: application/json" \
  -d '{
    "tenantId": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "avatar": "😀"
  }'
```

---

### 16. Get Participant Profile

Get a participant's global profile.

**Endpoint:** `GET /participants/{participantId}`

**Headers:**
```
Authorization: Bearer <participant_jwt_token>
```

**Path Parameters:**
- `participantId` - UUID of the participant

**Success Response (200):**
```json
{
  "participantId": "990e8400-e29b-41d4-a716-446655440004",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "avatar": "😀",
  "createdAt": "2024-01-20T11:00:00Z",
  "updatedAt": "2024-01-20T11:00:00Z"
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Unauthorized access
- `404` - Participant not found

---

### 17. Update Participant Profile

Update a participant's global profile.

**Endpoint:** `PUT /participants/{participantId}`

**Headers:**
```
Authorization: Bearer <participant_jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `participantId` - UUID of the participant

**Request Body:**
```json
{
  "name": "Jane Doe",
  "avatar": "😎"
}
```

**Success Response (200):**
```json
{
  "participantId": "990e8400-e29b-41d4-a716-446655440004",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Jane Doe",
  "avatar": "😎",
  "updatedAt": "2024-01-20T12:00:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body
- `401` - Missing or invalid token
- `403` - Unauthorized access
- `404` - Participant not found

---

### 18. Join Session

Join a quiz session (auto-creates session participation).

**Endpoint:** `POST /sessions/{sessionId}/join`

**Headers:**
```
Authorization: Bearer <participant_jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Success Response (201):**
```json
{
  "participationId": "aa0e8400-e29b-41d4-a716-446655440005",
  "participantId": "990e8400-e29b-41d4-a716-446655440004",
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "totalPoints": 0,
  "correctAnswers": 0,
  "joinedAt": "2024-01-20T11:30:00Z"
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Cross-tenant access denied
- `404` - Session not found

**Note:** This endpoint is idempotent. If the participant has already joined, it returns the existing participation.

---

### 19. Submit Answer

Submit an answer for a quiz round.

**Endpoint:** `POST /participants/answers`

**Headers:**
```
Authorization: Bearer <participant_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "roundNumber": 1,
  "answer": 2
}
```

**Success Response (201):**
```json
{
  "answerId": "bb0e8400-e29b-41d4-a716-446655440006",
  "participantId": "990e8400-e29b-41d4-a716-446655440004",
  "participationId": "aa0e8400-e29b-41d4-a716-446655440005",
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "roundNumber": 1,
  "answer": 2,
  "isCorrect": true,
  "points": 100,
  "submittedAt": "2024-01-20T11:35:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body
- `401` - Missing or invalid token
- `403` - Cross-tenant access denied
- `404` - Session or round not found

---

### 20. Get Scoreboard

Get the scoreboard for a quiz session.

**Endpoint:** `GET /sessions/{sessionId}/scoreboard`

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Success Response (200):**
```json
{
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "participants": [
    {
      "participantId": "990e8400-e29b-41d4-a716-446655440004",
      "name": "John Doe",
      "avatar": "😀",
      "totalPoints": 450,
      "correctAnswers": 5,
      "rank": 1
    },
    {
      "participantId": "cc0e8400-e29b-41d4-a716-446655440007",
      "name": "Jane Smith",
      "avatar": "😎",
      "totalPoints": 380,
      "correctAnswers": 4,
      "rank": 2
    }
  ]
}
```

**Error Responses:**
- `404` - Session not found

---

### 21. Delete Global Participant

Delete a global participant and all associated data.

**Endpoint:** `DELETE /participants/{participantId}`

**Headers:**
```
Authorization: Bearer <participant_jwt_token>
```

**Path Parameters:**
- `participantId` - UUID of the participant

**Success Response (200):**
```json
{
  "message": "Participant deleted successfully",
  "participantId": "990e8400-e29b-41d4-a716-446655440004"
}
```

**Error Responses:**
- `401` - Missing or invalid token
- `403` - Unauthorized access
- `404` - Participant not found

---

## Admin Endpoints

---

## Public Endpoints

### 22. Upload Audio File

Upload an audio file for use in quiz rounds.

**Endpoint:** `POST /admin/audio`

**Headers:**
```
Authorization: Bearer <tenant_admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "audioData": "base64_encoded_audio_data",
  "fileName": "song.mp3",
  "sessionId": "880e8400-e29b-41d4-a716-446655440003"
}
```

**Success Response (201):**
```json
{
  "audioKey": "sessions/880e8400-e29b-41d4-a716-446655440003/audio/abc123.mp3",
  "url": "https://presigned-s3-url..."
}
```

**Error Responses:**
- `400` - Invalid request body or missing fields
- `401` - Missing or invalid token
- `403` - Insufficient permissions or cross-tenant access
- `500` - Upload failed

---

### 23. Add Quiz Round

Add a round to an existing quiz session.

**Endpoint:** `POST /admin/sessions/{sessionId}/rounds`

**Headers:**
```
Authorization: Bearer <tenant_admin_jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Request Body:**
```json
{
  "audioKey": "sessions/880e8400-e29b-41d4-a716-446655440003/audio/abc123.mp3",
  "answers": [
    "Bohemian Rhapsody",
    "Stairway to Heaven",
    "Hotel California",
    "Sweet Child O' Mine"
  ],
  "correctAnswer": 0
}
```

**Success Response (201):**
```json
{
  "roundId": "dd0e8400-e29b-41d4-a716-446655440008",
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "audioKey": "sessions/880e8400-e29b-41d4-a716-446655440003/audio/abc123.mp3",
  "answers": [
    "Bohemian Rhapsody",
    "Stairway to Heaven",
    "Hotel California",
    "Sweet Child O' Mine"
  ],
  "correctAnswer": 0,
  "roundNumber": 1,
  "createdAt": "2024-01-20T12:00:00Z"
}
```

**Error Responses:**
- `400` - Invalid request body or validation error
- `401` - Missing or invalid token
- `403` - Insufficient permissions or cross-tenant access
- `404` - Session not found
- `409` - Maximum rounds (30) reached

---

### 24. Get QR Code Registration URL

Get the registration URL for a quiz session (used to generate QR codes).

**Endpoint:** `GET /sessions/{sessionId}/qr`

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Success Response (200):**
```json
{
  "registrationUrl": "https://musikquiz.example.com/register?sessionId=880e8400-e29b-41d4-a716-446655440003&tenantId=550e8400-e29b-41d4-a716-446655440000",
  "sessionId": "880e8400-e29b-41d4-a716-446655440003",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "sessionTitle": "80s Music Quiz"
}
```

**Error Responses:**
- `400` - Missing session ID
- `404` - Session not found

---

### 25. Get Audio File

Get a presigned URL to access an audio file.

**Endpoint:** `GET /audio/{audioKey}`

**Path Parameters:**
- `audioKey` - S3 object key (URL encoded)

**Success Response (302):**
Redirects to presigned S3 URL

**Response Body (200):**
```json
{
  "url": "https://presigned-s3-url..."
}
```

**Error Responses:**
- `400` - Missing audio key
- `404` - Audio file not found

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additionalInfo": "value"
    }
  }
}
```

### Common Error Codes

| Code                        | Status | Description                               |
| --------------------------- | ------ | ----------------------------------------- |
| `INVALID_REQUEST`           | 400    | Request body is missing or malformed      |
| `INVALID_JSON`              | 400    | Request body is not valid JSON            |
| `MISSING_FIELDS`            | 400    | Required fields are missing               |
| `INVALID_FIELD_VALUE`       | 400    | Field value doesn't meet requirements     |
| `INVALID_ANSWERS`           | 400    | Answers array is invalid                  |
| `INVALID_CORRECT_ANSWER`    | 400    | correctAnswer is not 0-3                  |
| `TENANT_INACTIVE`           | 400    | Tenant is inactive/deleted                |
| `INVALID_TENANT_ASSIGNMENT` | 400    | Invalid tenant ID provided                |
| `MISSING_TOKEN`             | 401    | Authorization header is missing           |
| `INVALID_TOKEN`             | 401    | JWT token is invalid                      |
| `TOKEN_EXPIRED`             | 401    | JWT token has expired                     |
| `INVALID_CREDENTIALS`       | 401    | Username or password is incorrect         |
| `INSUFFICIENT_PERMISSIONS`  | 403    | User doesn't have required role           |
| `CROSS_TENANT_ACCESS`       | 403    | Attempted to access another tenant's data |
| `TENANT_NOT_FOUND`          | 404    | Tenant doesn't exist                      |
| `ADMIN_NOT_FOUND`           | 404    | Admin doesn't exist                       |
| `PARTICIPANT_NOT_FOUND`     | 404    | Participant doesn't exist                 |
| `SESSION_NOT_FOUND`         | 404    | Quiz session doesn't exist                |
| `AUDIO_NOT_FOUND`           | 404    | Audio file doesn't exist                  |
| `DUPLICATE_USERNAME`        | 409    | Username already exists                   |
| `MAX_ROUNDS_REACHED`        | 409    | Session already has 30 rounds             |
| `DATABASE_ERROR`            | 500    | DynamoDB operation failed                 |
| `UPLOAD_ERROR`              | 500    | S3 upload failed                          |
| `INTERNAL_ERROR`            | 500    | Unexpected server error                   |

---

## Data Models

### Tenant

```typescript
{
  tenantId: string;         // UUID
  name: string;             // Tenant name
  description?: string;     // Optional description
  status: string;           // "active" | "inactive"
  createdAt: string;        // ISO 8601 timestamp
  updatedAt: string;        // ISO 8601 timestamp
  settings?: object;        // Tenant-specific configuration
}
```

### Admin

```typescript
{
  adminId: string;          // UUID
  tenantId?: string;        // UUID (null for super admins)
  username: string;         // Admin username
  passwordHash: string;     // Hashed password (bcrypt)
  role: string;             // "super_admin" | "tenant_admin"
  email?: string;           // Optional email
  createdAt: string;        // ISO 8601 timestamp
  updatedAt: string;        // ISO 8601 timestamp
}
```

### Global Participant

```typescript
{
  participantId: string;    // UUID
  tenantId: string;         // UUID
  name: string;             // Participant name
  avatar: string;           // Emoji avatar
  token: string;            // JWT token
  createdAt: string;        // ISO 8601 timestamp
  updatedAt: string;        // ISO 8601 timestamp
}
```

### Session Participation

```typescript
{
  participationId: string;  // UUID
  participantId: string;    // UUID (FK to GlobalParticipants)
  sessionId: string;        // UUID (FK to QuizSessions)
  tenantId: string;         // UUID (denormalized)
  joinedAt: string;         // ISO 8601 timestamp
  totalPoints: number;      // Session-specific score
  correctAnswers: number;   // Number of correct answers
}
```

### Quiz Session

```typescript
{
  sessionId: string;        // UUID
  tenantId: string;         // UUID
  title: string;            // Session title
  description: string;      // Session description
  createdBy: string;        // Admin ID who created it
  createdAt: string;        // ISO 8601 timestamp
  roundCount: number;       // Number of rounds (0-30)
  status: string;           // "draft" | "active" | "completed"
  currentRound?: number;    // Current round number
  rounds?: QuizRound[];     // Array of rounds (only in GET session)
}
```

### Quiz Round

```typescript
{
  roundId: string;          // UUID
  sessionId: string;        // Parent session UUID
  audioKey: string;         // S3 object key
  answers: string[];        // Array of 4 answer options
  correctAnswer: number;    // Index 0-3
  roundNumber: number;      // 1-30
  createdAt: string;        // ISO 8601 timestamp
}
```

### Answer

```typescript
{
  answerId: string;         // UUID
  participantId: string;    // UUID (references GlobalParticipants)
  participationId: string;  // UUID (FK to SessionParticipations)
  sessionId: string;        // UUID
  tenantId: string;         // UUID (denormalized)
  roundNumber: number;      // Round number
  answer: number;           // Selected answer index (0-3)
  isCorrect: boolean;       // Whether answer was correct
  points: number;           // Points earned
  submittedAt: string;      // ISO 8601 timestamp
}
```

---

## Multi-Tenancy

### Tenant Isolation

The system enforces strict tenant isolation:

1. **Data Separation**: All tenant-specific data includes a `tenantId` field
2. **Query Filtering**: All database queries filter by `tenantId`
3. **Access Control**: Cross-tenant access attempts return `403 Forbidden`
4. **Token Context**: JWT tokens include tenant information

### Tenant Context Flow

1. **Admin Login**: Admin receives token with `tenantId` and `role`
2. **Session Creation**: Sessions automatically inherit admin's `tenantId`
3. **Participant Registration**: Participants register with specific `tenantId`
4. **Session Join**: System validates participant and session share same `tenantId`
5. **Data Access**: All queries filtered by authenticated user's `tenantId`

### Backward Compatibility

The system supports legacy single-tenant deployments:

- **Default Tenant**: System creates a default tenant if none exist
- **Legacy Tokens**: Accepts tokens without `tenantId` (defaults to primary tenant)
- **Migration**: Scripts available to migrate existing data to multi-tenant model

---

## CORS Configuration

All endpoints support CORS with the following headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token
```

Preflight OPTIONS requests are automatically handled by API Gateway.

---

## Rate Limiting

API Gateway is configured with:
- Rate limit: 100 requests per second
- Burst limit: 200 requests

---

## Notes

- All timestamps are ISO 8601 format (e.g., `2024-01-20T10:00:00Z`)
- All UUIDs are version 4
- Audio files should be in MP3, WAV, or OGG format
- Maximum audio file size: 10MB (recommended)
- Session titles and descriptions support UTF-8
- Participant names support UTF-8
- JWT tokens expire after 24 hours
- Passwords must be at least 8 characters
- Tenant names are required, descriptions are optional

---

## Migration Guide

### Migrating from Single-Tenant to Multi-Tenant

If you have an existing single-tenant deployment:

1. **Deploy Updated Stack**: Deploy the new CDK stack with multi-tenant support
2. **Run Setup Script**: Execute `setup_default_tenant.py` to create default tenant
3. **Migrate Admins**: Run `migrate_admins.py` to associate admins with default tenant
4. **Migrate Sessions**: Run `migrate_sessions.py` to associate sessions with default tenant
5. **Migrate Participants**: Run `migrate_participants.py` to convert to global participants
6. **Migrate Answers**: Run `migrate_answers.py` to add tenant context to answers
7. **Verify**: Test all endpoints to ensure backward compatibility

See `scripts/MIGRATION_README.md` for detailed migration instructions.

---

## Examples

### Complete Workflow Example

#### 1. Super Admin Creates Tenant and Admin

```bash
# Login as super admin
curl -X POST https://YOUR_API/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"password"}'

# Create tenant
curl -X POST https://YOUR_API/super-admin/tenants \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Corp","description":"Corporate events"}'

# Create tenant admin
curl -X POST https://YOUR_API/super-admin/tenants/TENANT_ID/admins \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"acme_admin","password":"SecurePass123!","email":"admin@acme.com"}'
```

#### 2. Tenant Admin Creates Quiz Session

```bash
# Login as tenant admin
curl -X POST https://YOUR_API/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"acme_admin","password":"SecurePass123!"}'

# Create session (automatically associated with tenant)
curl -X POST https://YOUR_API/admin/sessions \
  -H "Authorization: Bearer TENANT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"80s Music Quiz","description":"Test your knowledge!"}'

# Add rounds...
```

#### 3. Participant Registers and Joins

```bash
# Register global participant
curl -X POST https://YOUR_API/participants/register \
  -H "Content-Type: application/json" \
  -d '{"tenantId":"TENANT_ID","name":"John Doe","avatar":"😀"}'

# Join session
curl -X POST https://YOUR_API/sessions/SESSION_ID/join \
  -H "Authorization: Bearer PARTICIPANT_TOKEN" \
  -H "Content-Type: application/json"

# Submit answer
curl -X POST https://YOUR_API/participants/answers \
  -H "Authorization: Bearer PARTICIPANT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"SESSION_ID","roundNumber":1,"answer":2}'

# View scoreboard
curl https://YOUR_API/sessions/SESSION_ID/scoreboard
```

---

## Support

For issues or questions:
- Check the migration guide in `scripts/MIGRATION_README.md`
- Review error codes in this documentation
- Check CloudWatch logs for detailed error information
- Verify tenant isolation is working correctly
