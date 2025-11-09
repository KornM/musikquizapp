# Music Quiz API Documentation

Base URL: `https://YOUR_API_GATEWAY_ID.execute-api.eu-central-1.amazonaws.com/prod`

## Table of Contents

- [Authentication](#authentication)
- [Admin Endpoints](#admin-endpoints)
- [Public Endpoints](#public-endpoints)
- [Error Responses](#error-responses)
- [Data Models](#data-models)

## Authentication

### Admin Authentication

Admin endpoints require a JWT token obtained through the login endpoint. Include the token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

Token expires after 24 hours.

---

## Admin Endpoints

### 1. Admin Login

Authenticate as an admin and receive a JWT token.

**Endpoint:** `POST /admin/login`

**Request Body:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Success Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 86400
}
```

**Error Responses:**
- `400` - Invalid request body or missing fields
- `401` - Invalid credentials

**Example:**
```bash
curl -X POST https://YOUR_API/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'
```

---

### 2. Create Quiz Session

Create a new quiz session.

**Endpoint:** `POST /admin/quiz-sessions`

**Headers:**
```
Authorization: Bearer <jwt_token>
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
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "title": "80s Music Quiz",
  "description": "Test your knowledge of 80s hits!",
  "createdBy": "admin-id",
  "createdAt": 1699024800,
  "roundCount": 0,
  "status": "draft"
}
```

**Error Responses:**
- `400` - Invalid request body
- `401` - Missing or invalid token
- `403` - Insufficient permissions

**Example:**
```bash
curl -X POST https://YOUR_API/admin/quiz-sessions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"80s Music Quiz","description":"Test your knowledge!"}'
```

---

### 3. Upload Audio File

Upload an audio file for use in quiz rounds.

**Endpoint:** `POST /admin/audio`

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "audioData": "base64_encoded_audio_data",
  "fileName": "song.mp3",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Success Response (201):**
```json
{
  "audioKey": "sessions/550e8400-e29b-41d4-a716-446655440000/audio/abc123.mp3",
  "url": "https://presigned-s3-url..."
}
```

**Error Responses:**
- `400` - Invalid request body or missing fields
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `500` - Upload failed

**Example:**
```bash
curl -X POST https://YOUR_API/admin/audio \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audioData": "'"$(base64 -i song.mp3)"'",
    "fileName": "song.mp3",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

### 4. Add Quiz Round

Add a round to an existing quiz session.

**Endpoint:** `POST /admin/quiz-sessions/{sessionId}/rounds`

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Request Body:**
```json
{
  "audioKey": "sessions/550e8400-e29b-41d4-a716-446655440000/audio/abc123.mp3",
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
  "roundId": "660e8400-e29b-41d4-a716-446655440001",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "audioKey": "sessions/550e8400-e29b-41d4-a716-446655440000/audio/abc123.mp3",
  "answers": [
    "Bohemian Rhapsody",
    "Stairway to Heaven",
    "Hotel California",
    "Sweet Child O' Mine"
  ],
  "correctAnswer": 0,
  "roundNumber": 1,
  "createdAt": 1699024900
}
```

**Error Responses:**
- `400` - Invalid request body or validation error
- `401` - Missing or invalid token
- `403` - Insufficient permissions
- `404` - Session not found
- `409` - Maximum rounds (30) reached

**Example:**
```bash
curl -X POST https://YOUR_API/admin/quiz-sessions/550e8400-e29b-41d4-a716-446655440000/rounds \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audioKey": "sessions/550e8400-e29b-41d4-a716-446655440000/audio/abc123.mp3",
    "answers": ["Song A", "Song B", "Song C", "Song D"],
    "correctAnswer": 0
  }'
```

---

## Public Endpoints

### 5. List Quiz Sessions

Get a list of all quiz sessions.

**Endpoint:** `GET /quiz-sessions`

**Success Response (200):**
```json
{
  "sessions": [
    {
      "sessionId": "550e8400-e29b-41d4-a716-446655440000",
      "title": "80s Music Quiz",
      "description": "Test your knowledge of 80s hits!",
      "createdBy": "admin-id",
      "createdAt": 1699024800,
      "roundCount": 5,
      "status": "active"
    },
    {
      "sessionId": "660e8400-e29b-41d4-a716-446655440001",
      "title": "90s Rock Quiz",
      "description": "Rock classics from the 90s",
      "createdBy": "admin-id",
      "createdAt": 1699020000,
      "roundCount": 10,
      "status": "draft"
    }
  ]
}
```

**Example:**
```bash
curl https://YOUR_API/quiz-sessions
```

---

### 6. Get Quiz Session

Get detailed information about a specific quiz session including all rounds.

**Endpoint:** `GET /quiz-sessions/{sessionId}`

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Success Response (200):**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "title": "80s Music Quiz",
  "description": "Test your knowledge of 80s hits!",
  "createdBy": "admin-id",
  "createdAt": 1699024800,
  "roundCount": 2,
  "status": "active",
  "rounds": [
    {
      "roundId": "660e8400-e29b-41d4-a716-446655440001",
      "sessionId": "550e8400-e29b-41d4-a716-446655440000",
      "audioKey": "sessions/550e8400-e29b-41d4-a716-446655440000/audio/abc123.mp3",
      "answers": ["Song A", "Song B", "Song C", "Song D"],
      "correctAnswer": 0,
      "roundNumber": 1,
      "createdAt": 1699024900
    },
    {
      "roundId": "770e8400-e29b-41d4-a716-446655440002",
      "sessionId": "550e8400-e29b-41d4-a716-446655440000",
      "audioKey": "sessions/550e8400-e29b-41d4-a716-446655440000/audio/def456.mp3",
      "answers": ["Artist 1", "Artist 2", "Artist 3", "Artist 4"],
      "correctAnswer": 2,
      "roundNumber": 2,
      "createdAt": 1699025000
    }
  ]
}
```

**Error Responses:**
- `400` - Missing session ID
- `404` - Session not found

**Example:**
```bash
curl https://YOUR_API/quiz-sessions/550e8400-e29b-41d4-a716-446655440000
```

---

### 7. Get QR Code Registration URL

Get the registration URL for a quiz session (used to generate QR codes).

**Endpoint:** `GET /quiz-sessions/{sessionId}/qr`

**Path Parameters:**
- `sessionId` - UUID of the quiz session

**Success Response (200):**
```json
{
  "registrationUrl": "https://musikquiz.example.com/register?sessionId=550e8400-e29b-41d4-a716-446655440000",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "sessionTitle": "80s Music Quiz"
}
```

**Error Responses:**
- `400` - Missing session ID
- `404` - Session not found

**Example:**
```bash
curl https://YOUR_API/quiz-sessions/550e8400-e29b-41d4-a716-446655440000/qr
```

---

### 8. Register Participant

Register a participant for a quiz session.

**Endpoint:** `POST /participants/register`

**Request Body:**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe"
}
```

**Success Response (201):**
```json
{
  "participantId": "880e8400-e29b-41d4-a716-446655440003",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "registeredAt": 1699025100
}
```

**Error Responses:**
- `400` - Invalid request body or missing fields
- `404` - Session not found

**Example:**
```bash
curl -X POST https://YOUR_API/participants/register \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe"
  }'
```

---

### 9. Get Audio File

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

**Example:**
```bash
curl https://YOUR_API/audio/sessions%2F550e8400-e29b-41d4-a716-446655440000%2Faudio%2Fabc123.mp3
```

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

| Code                       | Status | Description                          |
| -------------------------- | ------ | ------------------------------------ |
| `INVALID_REQUEST`          | 400    | Request body is missing or malformed |
| `INVALID_JSON`             | 400    | Request body is not valid JSON       |
| `MISSING_FIELDS`           | 400    | Required fields are missing          |
| `INVALID_ANSWERS`          | 400    | Answers array is invalid             |
| `INVALID_CORRECT_ANSWER`   | 400    | correctAnswer is not 0-3             |
| `MISSING_TOKEN`            | 401    | Authorization header is missing      |
| `INVALID_TOKEN`            | 401    | JWT token is invalid                 |
| `TOKEN_EXPIRED`            | 401    | JWT token has expired                |
| `INVALID_CREDENTIALS`      | 401    | Username or password is incorrect    |
| `INSUFFICIENT_PERMISSIONS` | 403    | User doesn't have required role      |
| `SESSION_NOT_FOUND`        | 404    | Quiz session doesn't exist           |
| `AUDIO_NOT_FOUND`          | 404    | Audio file doesn't exist             |
| `MAX_ROUNDS_REACHED`       | 409    | Session already has 30 rounds        |
| `DATABASE_ERROR`           | 500    | DynamoDB operation failed            |
| `UPLOAD_ERROR`             | 500    | S3 upload failed                     |
| `INTERNAL_ERROR`           | 500    | Unexpected server error              |

---

## Data Models

### Quiz Session

```typescript
{
  sessionId: string;        // UUID
  title: string;            // Session title
  description: string;      // Session description
  createdBy: string;        // Admin ID who created it
  createdAt: number;        // Unix timestamp
  roundCount: number;       // Number of rounds (0-30)
  status: string;           // "draft" | "active" | "completed"
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
  createdAt: number;        // Unix timestamp
}
```

### Participant

```typescript
{
  participantId: string;    // UUID
  sessionId: string;        // Quiz session UUID
  name: string;             // Participant name
  token: string;            // JWT token
  registeredAt: number;     // Unix timestamp
}
```

### Admin

```typescript
{
  adminId: string;          // UUID
  username: string;         // Admin username
  passwordHash: string;     // Hashed password (PBKDF2-SHA256)
  createdAt: number;        // Unix timestamp
}
```

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

- All timestamps are Unix timestamps (seconds since epoch)
- All UUIDs are version 4
- Audio files should be in MP3, WAV, or OGG format
- Maximum audio file size: 10MB (recommended)
- Session titles and descriptions support UTF-8
- Participant names support UTF-8
- JWT tokens expire after 24 hours
