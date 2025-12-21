# Shrutik Architecture Overview

This document provides a comprehensive overview of Shrutik's system architecture, design principles, and technical decisions.

## System Architecture

Shrutik follows a modern, microservices-inspired architecture with clear separation of concerns and scalable design patterns.

### High-Level Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        WEB[React Frontend]
        MOBILE[Mobile App]
        API_DOCS[API Documentation]
    end

    subgraph "API Gateway Layer"
        NGINX[Nginx Reverse Proxy]
        RATE_LIMIT[Rate Limiting]
        AUTH_MW[Authentication Middleware]
    end

    subgraph "Application Layer"
        API[FastAPI Backend]
        WORKER[Celery Workers]
        SCHEDULER[Task Scheduler]
    end

    subgraph "Business Logic Layer"
        AUTH_SVC[Authentication Service]
        VOICE_SVC[Voice Recording Service]
        TRANS_SVC[Transcription Service]
        CONSENSUS_SVC[Consensus Service]
        EXPORT_SVC[Export Service]
        ADMIN_SVC[Admin Service]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis)]
        FILES[File Storage]
    end

    subgraph "External Services"
        CDN[Content Delivery Network]
        EMAIL[Email Service]
        MONITORING[Monitoring & Logging]
    end

    WEB --> NGINX
    MOBILE --> NGINX
    NGINX --> API
    API --> AUTH_SVC
    API --> VOICE_SVC
    API --> TRANS_SVC
    WORKER --> CONSENSUS_SVC
    WORKER --> EXPORT_SVC
    
    AUTH_SVC --> POSTGRES
    VOICE_SVC --> POSTGRES
    VOICE_SVC --> FILES
    TRANS_SVC --> POSTGRES
    TRANS_SVC --> REDIS
    
    API --> REDIS
    WORKER --> REDIS
    
    FILES --> CDN
    API --> EMAIL
    API --> MONITORING
```

## Design Principles

### 1. Modularity
- **Service-Oriented**: Clear separation between different business domains
- **Loose Coupling**: Services communicate through well-defined interfaces
- **High Cohesion**: Related functionality grouped together

### 2. Scalability
- **Horizontal Scaling**: Stateless services that can be scaled independently
- **Async Processing**: Heavy operations handled by background workers
- **Caching Strategy**: Multi-layer caching for performance optimization

### 3. Reliability
- **Error Handling**: Comprehensive error handling and recovery mechanisms
- **Health Checks**: Automated monitoring and alerting
- **Data Integrity**: ACID transactions and data validation

### 4. Security
- **Authentication**: JWT-based authentication with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Protection**: Encryption at rest and in transit

### 5. Maintainability
- **Clean Code**: Following Python and TypeScript best practices
- **Documentation**: Comprehensive API and code documentation
- **Testing**: High test coverage with unit, integration, and E2E tests

## Technology Stack

### Backend Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | FastAPI | High-performance async API framework |
| **Database** | PostgreSQL | Primary data storage with ACID compliance |
| **Cache/Queue** | Redis | Caching, session storage, and message queue |
| **Background Jobs** | Celery | Async task processing |
| **Audio Processing** | Librosa, PyDub | Audio analysis and manipulation |
| **Authentication** | JWT | Stateless authentication |
| **Validation** | Pydantic | Data validation and serialization |
| **ORM** | SQLAlchemy | Database abstraction layer |
| **Migrations** | Alembic | Database schema migrations |

### Frontend Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | React 18 | Component-based UI framework |
| **Meta Framework** | Next.js | Full-stack React framework |
| **Language** | TypeScript | Type-safe JavaScript |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **State Management** | Zustand | Lightweight state management |
| **HTTP Client** | Axios | Promise-based HTTP client |
| **Audio Recording** | MediaRecorder API | Browser audio recording |
| **Testing** | Jest, React Testing Library | Unit and integration testing |

### Infrastructure Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containerization** | Docker | Application containerization |
| **Orchestration** | Docker Compose | Multi-container application management |
| **Reverse Proxy** | Nginx | Load balancing and SSL termination |
| **Monitoring** | Prometheus, Grafana | Metrics collection and visualization |
| **Logging** | Structured logging | Centralized log management |
| **CI/CD** | GitHub Actions | Automated testing and deployment |

## Data Architecture

### Database Schema Design

```mermaid
erDiagram
    %% Core Relationships
    USERS ||--o{ VOICE_RECORDINGS : "creates"
    USERS ||--o{ TRANSCRIPTIONS : "creates"
    USERS ||--o{ QUALITY_REVIEWS : "performs"
    USERS ||--o{ EXPORT_AUDIT_LOGS : "performs"
    USERS ||--o{ EXPORT_DOWNLOADS : "downloads"
    USERS ||--o| EXPORT_BATCHES : "creates (optional)"

    LANGUAGES ||--o{ SCRIPTS : "has"
    LANGUAGES ||--o{ VOICE_RECORDINGS : "recorded in"
    LANGUAGES ||--o{ TRANSCRIPTIONS : "transcribed in"

    SCRIPTS ||--o{ VOICE_RECORDINGS : "recorded from"

    VOICE_RECORDINGS ||--|{ AUDIO_CHUNKS : "divided into (1 to many)"

    AUDIO_CHUNKS ||--o{ TRANSCRIPTIONS : "has many"
    AUDIO_CHUNKS ||--o| TRANSCRIPTIONS : "has one consensus"

    TRANSCRIPTIONS ||--o{ QUALITY_REVIEWS : "reviewed by"

    EXPORT_BATCHES ||--o{ EXPORT_AUDIT_LOGS : "generates"
    EXPORT_BATCHES ||--o{ EXPORT_DOWNLOADS : "downloaded by"

    %% Entities with attributes
    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        string role "(enum: userrole)"
        json meta_data
        timestamptz created_at
        timestamptz updated_at
    }

    LANGUAGES {
        int id PK
        string name
        string code UK
        timestamptz created_at
    }

    SCRIPTS {
        int id PK
        int language_id FK
        text text
        string duration_category "(enum: durationcategory)"
        json meta_data
        timestamptz created_at
        timestamptz updated_at
    }

    VOICE_RECORDINGS {
        int id PK
        int user_id FK
        int script_id FK
        int language_id FK
        string file_path
        float duration
        string status "(enum: recordingstatus)"
        json meta_data
        timestamptz created_at
        timestamptz updated_at
    }

    AUDIO_CHUNKS {
        int id PK
        int recording_id FK
        int chunk_index
        string file_path
        float start_time
        float end_time
        float duration
        text sentence_hint
        json meta_data
        timestamptz created_at
        int transcript_count
        boolean ready_for_export
        float consensus_quality
        int consensus_transcript_id FK "optional"
        int consensus_failed_count
    }

    TRANSCRIPTIONS {
        int id PK
        int chunk_id FK
        int user_id FK
        int language_id FK
        text text
        float quality
        float confidence
        boolean is_consensus
        boolean is_validated
        json meta_data
        timestamptz created_at
        timestamptz updated_at
    }

    QUALITY_REVIEWS {
        int id PK
        int transcription_id FK
        int reviewer_id FK
        string decision "(enum: reviewdecision)"
        float rating
        text comment
        json meta_data
        timestamptz created_at
    }

    EXPORT_BATCHES {
        int id PK
        string batch_id UK
        string archive_path
        string storage_type "(enum: storagetype)"
        int chunk_count
        bigint file_size_bytes
        json chunk_ids
        string status "(enum: exportbatchstatus)"
        boolean exported
        text error_message
        int retry_count
        string checksum
        int compression_level
        string format_version
        json recording_id_range
        json language_stats
        float total_duration_seconds
        json filter_criteria
        timestamptz created_at
        timestamptz completed_at
        int created_by_id FK "optional"
    }

    EXPORT_AUDIT_LOGS {
        int id PK
        string export_id
        int user_id FK
        string export_type
        string format
        json filters_applied
        int records_exported
        bigint file_size_bytes
        string ip_address
        string user_agent
        timestamptz created_at
    }

    EXPORT_DOWNLOADS {
        int id PK
        string batch_id FK
        int user_id FK
        timestamptz downloaded_at
        string ip_address
        string user_agent
    }
```

### Data Flow Patterns

#### 1. Voice Recording Data Flow
```
User Input → Frontend → API → Database → File Storage → Background Processing → Chunking → Database Update
```

#### 2. Transcription Data Flow
```
User Request → API → Database Query → Cache Check → Response → User Input → Validation → Database Save → Consensus Trigger
```

#### 3. Consensus Calculation Flow
```
Transcription Submit → Background Job → Collect Related → Calculate Similarity → Weight Quality → Update Consensus → Notify Users
```

## API Design

### RESTful API Principles

Shrutik follows REST architectural principles with some pragmatic adaptations:

- **Resource-Based URLs**: `/api/recordings`, `/api/transcriptions`
- **HTTP Methods**: GET, POST, PUT, DELETE for CRUD operations
- **Status Codes**: Proper HTTP status codes for different scenarios
- **JSON Format**: Consistent JSON request/response format
- **Pagination**: Cursor-based pagination for large datasets
- **Versioning**: API versioning through URL path (`/api/v1/`)

### API Structure

```
/api/
├── auth/
│   ├── POST /login
│   ├── POST /register
│   ├── POST /refresh
│   └── POST /logout
├── recordings/
│   ├── GET /
│   ├── POST /sessions
│   ├── POST /upload
│   └── GET /{id}/progress
├── transcriptions/
│   ├── GET /
│   ├── POST /tasks
│   ├── POST /submit
│   └── POST /skip
├── chunks/
│   ├── GET /{id}/audio
│   └── GET /{id}/info
├── admin/
│   ├── GET /stats/platform
│   ├── GET /users
│   └── GET /performance/dashboard
└── export/
    ├── POST /dataset
    └── GET /jobs/{id}/status
```

### Authentication & Authorization

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant Auth as Auth Service
    participant DB as Database

    C->>A: POST /auth/login
    A->>Auth: Validate Credentials
    Auth->>DB: Check User
    DB-->>Auth: User Data
    Auth->>Auth: Generate JWT
    Auth-->>A: JWT + Refresh Token
    A-->>C: Authentication Response

    Note over C: Store JWT in memory/secure storage

    C->>A: GET /recordings (with JWT)
    A->>Auth: Validate JWT
    Auth->>Auth: Check Expiry & Signature
    Auth-->>A: User Context
    A->>A: Check Permissions
    A-->>C: Protected Resource
```

## Performance Architecture

### Caching Strategy

```mermaid
graph LR
    subgraph "Client Side"
        BROWSER[Browser Cache]
        LOCAL[Local Storage]
    end
    
    subgraph "CDN Layer"
        CDN[Content Delivery Network]
    end
    
    subgraph "Application Layer"
        API_CACHE[API Response Cache]
        DB_CACHE[Database Query Cache]
        SESSION[Session Cache]
    end
    
    subgraph "Database Layer"
        DB[(PostgreSQL)]
        REDIS[(Redis)]
    end
    
    BROWSER --> CDN
    CDN --> API_CACHE
    API_CACHE --> DB_CACHE
    DB_CACHE --> REDIS
    SESSION --> REDIS
    DB_CACHE --> DB
```

### Performance Optimizations

#### Backend Optimizations
- **Connection Pooling**: Database connection pooling with configurable limits
- **Query Optimization**: Indexed queries and efficient SQL patterns
- **Async Processing**: Non-blocking I/O for concurrent request handling
- **Background Jobs**: Heavy operations moved to background workers
- **Response Compression**: Gzip compression for API responses

#### Frontend Optimizations
- **Code Splitting**: Dynamic imports for reduced bundle size
- **Lazy Loading**: Components and routes loaded on demand
- **Image Optimization**: Optimized images with Next.js Image component
- **Caching**: Aggressive caching of static assets and API responses
- **Service Workers**: Offline functionality and background sync

#### Database Optimizations
- **Indexing Strategy**: Proper indexes on frequently queried columns
- **Query Optimization**: Efficient queries with proper joins and filters
- **Read Replicas**: Separate read replicas for analytics queries
- **Partitioning**: Table partitioning for large datasets

## Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Network Security"
        FIREWALL[Firewall Rules]
        DDoS[DDoS Protection]
        SSL[SSL/TLS Encryption]
    end
    
    subgraph "Application Security"
        AUTH[Authentication]
        AUTHZ[Authorization]
        VALIDATION[Input Validation]
        SANITIZATION[Data Sanitization]
    end
    
    subgraph "Data Security"
        ENCRYPTION[Encryption at Rest]
        BACKUP[Secure Backups]
        AUDIT[Audit Logging]
    end
    
    FIREWALL --> AUTH
    DDoS --> AUTH
    SSL --> AUTH
    AUTH --> ENCRYPTION
    AUTHZ --> ENCRYPTION
    VALIDATION --> BACKUP
    SANITIZATION --> AUDIT
```

### Security Measures

#### Authentication & Authorization
- **JWT Tokens**: Stateless authentication with short-lived access tokens
- **Refresh Tokens**: Secure token refresh mechanism
- **Role-Based Access**: Granular permissions based on user roles
- **Session Management**: Secure session handling with Redis

#### Data Protection
- **Input Validation**: Comprehensive input validation using Pydantic
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **XSS Protection**: Content Security Policy and input sanitization
- **CSRF Protection**: CSRF tokens for state-changing operations

#### Infrastructure Security
- **HTTPS Enforcement**: All communications encrypted with TLS
- **Security Headers**: Comprehensive security headers implementation
- **Rate Limiting**: Protection against abuse and DoS attacks
- **File Upload Security**: Secure file upload with type validation

## Monitoring & Observability

### Monitoring Stack

```mermaid
graph LR
    subgraph "Application"
        APP[Shrutik Application]
        METRICS[Metrics Collection]
        LOGS[Structured Logging]
        TRACES[Distributed Tracing]
    end
    
    subgraph "Collection"
        PROMETHEUS[Prometheus]
        LOKI[Loki]
        JAEGER[Jaeger]
    end
    
    subgraph "Visualization"
        GRAFANA[Grafana Dashboards]
        ALERTS[Alert Manager]
    end
    
    APP --> METRICS
    APP --> LOGS
    APP --> TRACES
    
    METRICS --> PROMETHEUS
    LOGS --> LOKI
    TRACES --> JAEGER
    
    PROMETHEUS --> GRAFANA
    LOKI --> GRAFANA
    JAEGER --> GRAFANA
    
    PROMETHEUS --> ALERTS
```

### Key Metrics

#### Application Metrics
- **Request Rate**: Requests per second by endpoint
- **Response Time**: P50, P95, P99 response times
- **Error Rate**: Error percentage by endpoint and status code
- **Throughput**: Data processing throughput

#### Business Metrics
- **User Engagement**: Active users, session duration
- **Data Quality**: Transcription accuracy, consensus rates
- **System Usage**: Recording uploads, transcription submissions
- **Performance**: Audio processing times, consensus calculation speed

#### Infrastructure Metrics
- **System Resources**: CPU, memory, disk usage
- **Database Performance**: Query times, connection pool status
- **Cache Performance**: Hit rates, memory usage
- **Network**: Bandwidth usage, connection counts

## Deployment Architecture

### Environment Strategy

```mermaid
graph LR
    subgraph "Development"
        DEV_LOCAL[Local Development]
        DEV_DOCKER[Docker Development]
    end
    
    subgraph "Testing"
        TEST_UNIT[Unit Tests]
        TEST_INTEGRATION[Integration Tests]
        TEST_E2E[E2E Tests]
    end
    
    subgraph "Staging"
        STAGING[Staging Environment]
        UAT[User Acceptance Testing]
    end
    
    subgraph "Production"
        PROD[Production Environment]
        MONITORING[Production Monitoring]
    end
    
    DEV_LOCAL --> TEST_UNIT
    DEV_DOCKER --> TEST_INTEGRATION
    TEST_UNIT --> TEST_E2E
    TEST_INTEGRATION --> STAGING
    TEST_E2E --> STAGING
    STAGING --> UAT
    UAT --> PROD
    PROD --> MONITORING
```

### Deployment Pipeline

1. **Code Commit**: Developer pushes code to repository
2. **Automated Testing**: Unit, integration, and E2E tests run
3. **Build Process**: Docker images built and tagged
4. **Staging Deployment**: Automatic deployment to staging
5. **Manual Testing**: QA and user acceptance testing
6. **Production Deployment**: Manual approval and deployment
7. **Health Checks**: Automated health verification
8. **Monitoring**: Continuous monitoring and alerting

## Future Architecture Considerations

### Scalability Enhancements
- **Microservices**: Further decomposition into microservices
- **Event-Driven Architecture**: Event sourcing and CQRS patterns
- **Kubernetes**: Container orchestration for better scaling
- **Service Mesh**: Advanced service-to-service communication

### Performance Improvements
- **Edge Computing**: Edge nodes for global content delivery
- **Advanced Caching**: Distributed caching with Redis Cluster
- **Database Sharding**: Horizontal database partitioning
- **GraphQL**: More efficient data fetching

### AI/ML Integration
- **Automated Quality Assessment**: ML-based quality scoring
- **Smart Chunk Assignment**: AI-driven task assignment
- **Real-time Transcription**: Automatic transcription assistance
- **Anomaly Detection**: ML-based fraud and quality detection

---

This architecture provides a solid foundation for Shrutik's current needs while maintaining flexibility for future growth and enhancements.
