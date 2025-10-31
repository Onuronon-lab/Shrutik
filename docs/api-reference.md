# API Reference

This document provides comprehensive documentation for the Shrutik API, including authentication, endpoints, request/response formats, and examples.

## 🔗 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`

## 🔐 Authentication

Shrutik uses JWT (JSON Web Token) based authentication with refresh tokens for secure API access.

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant DB as Database

    C->>A: POST /api/auth/login
    A->>DB: Validate credentials
    DB-->>A: User data
    A-->>C: JWT + Refresh Token

    Note over C: Store tokens securely

    C->>A: GET /api/recordings (with JWT)
    A->>A: Validate JWT
    A-->>C: Protected resource

    Note over C: JWT expires

    C->>A: POST /api/auth/refresh
    A->>A: Validate refresh token
    A-->>C: New JWT
```

### Authentication Endpoints

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "contributor"
  }
}
```

#### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "secure_password",
  "name": "Jane Smith",
  "preferred_language": "bn"
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Logout
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

### Using Authentication

Include the JWT token in the Authorization header for all protected endpoints:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📊 Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "data": {
    // Response data
  },
  "message": "Operation successful",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Pagination Response
```json
{
  "data": [
    // Array of items
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## 🎤 Voice Recordings API

### Create Recording Session

Start a new recording session for a specific script.

```http
POST /api/recordings/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "script_id": 123,
  "language_id": 1,
  "metadata": {
    "device_info": "iPhone 14",
    "environment": "quiet_room"
  }
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "script": {
    "id": 123,
    "content": "আমি বাংলায় কথা বলি।",
    "language": "Bengali",
    "difficulty": "easy"
  },
  "expires_at": "2024-01-01T14:00:00Z"
}
```

### Upload Recording

Upload an audio file for a recording session.

```http
POST /api/recordings/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

session_id: uuid-string
duration: 5.2
audio_format: wav
file_size: 1048576
sample_rate: 44100
channels: 1
audio_file: <binary_data>
```

**Response:**
```json
{
  "recording_id": 456,
  "status": "uploaded",
  "processing_job_id": "job-uuid",
  "estimated_processing_time": 30
}
```

### Get User Recordings

Retrieve paginated list of user's recordings.

```http
GET /api/recordings?skip=0&limit=20&status=processed
Authorization: Bearer <token>
```

**Response:**
```json
{
  "recordings": [
    {
      "id": 456,
      "script_id": 123,
      "language": "Bengali",
      "duration": 5.2,
      "status": "processed",
      "chunks_count": 3,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

### Get Recording Progress

Check processing progress for a recording.

```http
GET /api/recordings/456/progress
Authorization: Bearer <token>
```

**Response:**
```json
{
  "recording_id": 456,
  "status": "processing",
  "progress_percentage": 75,
  "current_step": "chunking_audio",
  "estimated_completion": "2024-01-01T12:05:00Z",
  "chunks_created": 2
}
```

## 📝 Transcriptions API

### Get Transcription Task

Request audio chunks for transcription.

```http
POST /api/transcriptions/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity": 5,
  "language_id": 1,
  "skip_chunk_ids": [10, 15, 20],
  "difficulty_preference": "mixed"
}
```

**Response:**
```json
{
  "session_id": "transcription-session-uuid",
  "chunks": [
    {
      "id": 789,
      "recording_id": 456,
      "chunk_index": 1,
      "file_path": "/chunks/chunk_789.wav",
      "duration": 3.5,
      "sentence_hint": "Greeting phrase",
      "transcription_count": 2
    }
  ],
  "total_available": 1500
}
```

### Submit Transcriptions

Submit transcriptions for audio chunks.

```http
POST /api/transcriptions/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "transcription-session-uuid",
  "transcriptions": [
    {
      "chunk_id": 789,
      "language_id": 1,
      "text": "আমি বাংলায় কথা বলি।",
      "quality": 4.5,
      "confidence": 0.95,
      "metadata": {
        "time_taken": 45,
        "difficulty_rating": 3
      }
    }
  ],
  "skipped_chunk_ids": [790]
}
```

**Response:**
```json
{
  "submitted_count": 1,
  "skipped_count": 1,
  "transcriptions": [
    {
      "id": 1001,
      "chunk_id": 789,
      "text": "আমি বাংলায় কথা বলি।",
      "quality": 4.5,
      "is_consensus": false,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "message": "Successfully submitted 1 transcriptions"
}
```

### Skip Chunk

Skip a difficult or unclear audio chunk.

```http
POST /api/transcriptions/skip
Authorization: Bearer <token>
Content-Type: application/json

{
  "chunk_id": 790,
  "reason": "poor_audio_quality",
  "comment": "Background noise makes it unclear"
}
```

### Get User Transcriptions

Retrieve user's transcription history.

```http
GET /api/transcriptions?skip=0&limit=20&language_id=1
Authorization: Bearer <token>
```

**Response:**
```json
{
  "transcriptions": [
    {
      "id": 1001,
      "chunk_id": 789,
      "text": "আমি বাংলায় কথা বলি।",
      "quality": 4.5,
      "confidence": 0.95,
      "is_consensus": true,
      "is_validated": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

## 🎵 Audio Chunks API

### Get Chunk Audio

Retrieve audio file for a specific chunk.

```http
GET /api/chunks/789/audio
Authorization: Bearer <token>
```

**Response:** Binary audio data with optimized headers

**Headers:**
```
Content-Type: audio/wav
Cache-Control: public, max-age=3600
Accept-Ranges: bytes
Content-Length: 1048576
```

### Get Chunk Info

Get metadata about an audio chunk.

```http
GET /api/chunks/789/info
Authorization: Bearer <token>
```

**Response:**
```json
{
  "chunk_id": 789,
  "recording_id": 456,
  "duration": 3.5,
  "start_time": 1.2,
  "end_time": 4.7,
  "transcription_count": 3,
  "file_size": 1048576,
  "optimized_url": "https://cdn.example.com/chunks/789.wav",
  "alternatives": [
    {
      "format": ".mp3",
      "url": "https://cdn.example.com/chunks/789.mp3",
      "mime_type": "audio/mpeg"
    }
  ]
}
```

## 👥 Admin API

### Platform Statistics

Get comprehensive platform statistics (admin only).

```http
GET /api/admin/stats/platform
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "users": {
    "total": 1500,
    "active_last_30_days": 450,
    "new_this_month": 75
  },
  "recordings": {
    "total": 5000,
    "total_duration_hours": 250.5,
    "processed": 4800,
    "pending": 200
  },
  "transcriptions": {
    "total": 15000,
    "consensus_reached": 12000,
    "average_quality": 4.2
  },
  "languages": {
    "supported": 5,
    "most_active": "Bengali"
  }
}
```

### User Management

Get users for management (admin only).

```http
GET /api/admin/users?role=contributor&limit=50
Authorization: Bearer <admin_token>
```

### Performance Dashboard

Get performance metrics (admin only).

```http
GET /api/admin/performance/dashboard
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "system_metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "active_connections": 150
  },
  "cache_performance": {
    "hit_rate": 85.5,
    "memory_used": "512MB",
    "keys_count": 15000
  },
  "database_performance": {
    "connection_pool": {
      "total_connections": 20,
      "active_connections": 8,
      "idle_connections": 12
    },
    "slow_queries": 2
  }
}
```

## 📤 Export API

### Create Dataset Export

Request a dataset export job.

```http
POST /api/export/dataset
Authorization: Bearer <token>
Content-Type: application/json

{
  "format": "csv",
  "language_ids": [1, 2],
  "include_audio": true,
  "quality_threshold": 4.0,
  "consensus_only": true,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  }
}
```

**Response:**
```json
{
  "job_id": "export-job-uuid",
  "status": "queued",
  "estimated_completion": "2024-01-01T12:30:00Z",
  "estimated_size_mb": 150
}
```

### Get Export Status

Check export job status.

```http
GET /api/export/jobs/export-job-uuid/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "job_id": "export-job-uuid",
  "status": "completed",
  "progress_percentage": 100,
  "download_url": "https://api.example.com/downloads/dataset-uuid.zip",
  "file_size_mb": 145.7,
  "expires_at": "2024-01-08T12:00:00Z"
}
```

## 📋 Scripts API

### Get Available Scripts

Retrieve scripts available for recording.

```http
GET /api/scripts?language_id=1&difficulty=easy&limit=20
Authorization: Bearer <token>
```

**Response:**
```json
{
  "scripts": [
    {
      "id": 123,
      "content": "আমি বাংলায় কথা বলি।",
      "language": {
        "id": 1,
        "name": "Bengali",
        "code": "bn"
      },
      "difficulty": "easy",
      "estimated_duration": 3.5,
      "recording_count": 25
    }
  ],
  "total": 500,
  "page": 1,
  "per_page": 20
}
```

## 🌐 Languages API

### Get Supported Languages

Retrieve list of supported languages.

```http
GET /api/languages
```

**Response:**
```json
{
  "languages": [
    {
      "id": 1,
      "name": "Bengali",
      "code": "bn",
      "script": "Bengali",
      "active": true,
      "recording_count": 5000,
      "transcription_count": 15000
    },
    {
      "id": 2,
      "name": "Hindi",
      "code": "hi",
      "script": "Devanagari",
      "active": true,
      "recording_count": 3000,
      "transcription_count": 9000
    }
  ]
}
```

## 🔍 Search API

### Search Transcriptions

Search through transcriptions (admin only).

```http
GET /api/search/transcriptions?q=greeting&language_id=1&limit=20
Authorization: Bearer <admin_token>
```

## ❤️ Health Check

### System Health

Check system health and status.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": true,
    "redis": true,
    "disk_space": true,
    "memory": true
  },
  "performance": {
    "database_pool": {
      "total_connections": 20,
      "active_connections": 5
    },
    "cache_status": true
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 📊 Metrics

### Performance Metrics

Get performance metrics (admin only).

```http
GET /metrics
Authorization: Bearer <admin_token>
```

## 🚨 Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

### Custom Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `AUTHENTICATION_FAILED` | Invalid credentials |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SESSION_EXPIRED` | Recording/transcription session expired |
| `FILE_TOO_LARGE` | Uploaded file exceeds size limit |
| `UNSUPPORTED_FORMAT` | Audio format not supported |
| `PROCESSING_ERROR` | Audio processing failed |
| `CONSENSUS_PENDING` | Transcription consensus not yet reached |

## 🔧 Rate Limits

### Default Limits

| User Type | Requests/Minute |
|-----------|-----------------|
| Anonymous | 60 |
| Authenticated | 300 |
| Admin | 1000 |
| Sworik Developer | 2000 |

### Endpoint-Specific Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/login` | 10/min | 1 minute |
| `/api/recordings/upload` | 20/min | 1 minute |
| `/api/transcriptions/submit` | 100/min | 1 minute |
| `/api/chunks/*/audio` | 10/sec | 1 second |

### Rate Limit Headers

```http
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## 🔒 Security

### API Security Best Practices

1. **Always use HTTPS** in production
2. **Store JWT tokens securely** (not in localStorage for web apps)
3. **Implement proper CORS** policies
4. **Validate all inputs** on client and server
5. **Use refresh tokens** for long-lived sessions
6. **Implement rate limiting** to prevent abuse
7. **Log security events** for monitoring

### Content Security Policy

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; media-src 'self' blob:; connect-src 'self' wss:
```

## 📚 SDKs and Libraries

### JavaScript/TypeScript SDK

```bash
npm install @shrutik/sdk
```

```typescript
import { ShrutikClient } from '@shrutik/sdk';

const client = new ShrutikClient({
  baseURL: 'https://api.yourdomain.com',
  apiKey: 'your-api-key'
});

// Get transcription task
const task = await client.transcriptions.getTask({
  quantity: 5,
  languageId: 1
});

// Submit transcription
await client.transcriptions.submit({
  sessionId: task.sessionId,
  transcriptions: [{
    chunkId: 789,
    text: 'Transcribed text',
    quality: 4.5
  }]
});
```

### Python SDK

```bash
pip install shrutik-sdk
```

```python
from shrutik import ShrutikClient

client = ShrutikClient(
    base_url='https://api.yourdomain.com',
    api_key='your-api-key'
)

# Get transcription task
task = client.transcriptions.get_task(
    quantity=5,
    language_id=1
)

# Submit transcription
client.transcriptions.submit(
    session_id=task.session_id,
    transcriptions=[{
        'chunk_id': 789,
        'text': 'Transcribed text',
        'quality': 4.5
    }]
)
```

## 🧪 Testing

### API Testing with curl

```bash
# Login
curl -X POST https://api.yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Get recordings (with token)
curl -X GET https://api.yourdomain.com/api/recordings \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Upload recording
curl -X POST https://api.yourdomain.com/api/recordings/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "session_id=uuid" \
  -F "duration=5.2" \
  -F "audio_format=wav" \
  -F "file_size=1048576" \
  -F "audio_file=@recording.wav"
```

### Postman Collection

Import our [Postman collection](https://api.yourdomain.com/postman/shrutik-api.json) for easy API testing.

---

This API reference provides comprehensive documentation for integrating with Shrutik. For additional support, join our [Discord community](https://discord.gg/9hZ9eW8ARk) or check our [GitHub repository](https://github.com/Onuronon-lab/Shrutik).