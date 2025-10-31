# Changelog

All notable changes to Shrutik will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- mdBook documentation site with GitHub Pages hosting
- Comprehensive troubleshooting guide
- FAQ section with common questions and answers
- Environment configuration files for different deployment scenarios
- Admin user creation script with interactive and non-interactive modes
- System logging API endpoints for administrators
- Performance monitoring and optimization features
- Redis-based caching system with multi-layer support
- Rate limiting with role-based controls
- CDN integration for optimized audio delivery
- Database connection pooling and optimization
- Comprehensive error handling and logging system

### Changed
- Rebranded from "Voice Data Collection Platform" to "Shrutik (শ্রুতিক)"
- Updated all documentation to reflect correct database names and service configurations
- Improved Docker development workflow with dedicated environment files
- Enhanced admin API with comprehensive system monitoring endpoints
- Standardized environment variable configuration across all deployment methods

### Fixed
- Alembic configuration to use environment variables instead of hardcoded values
- Docker service name consistency between compose files
- Database name standardization across all configuration files
- Documentation links and references to existing files
- Environment file templates with correct service names and database names

### Security
- Enhanced password validation in admin creation script
- Improved input validation across all API endpoints
- Added comprehensive rate limiting to prevent abuse
- Implemented secure session management with JWT tokens

## [1.0.0] - 2024-11-01

### Added
- Initial release of Shrutik voice data collection platform
- FastAPI backend with comprehensive REST API
- Next.js frontend with modern React components
- PostgreSQL database with Alembic migrations
- Redis integration for caching and background jobs
- Celery for asynchronous task processing
- Docker and Docker Compose support
- User authentication and authorization system
- Role-based access control (Admin, Sworik, Contributor)
- Audio file upload and processing
- Voice recording functionality
- Transcription system with consensus mechanism
- Quality review and rating system
- Multi-language support with Bengali as default
- Admin dashboard for user and content management
- Comprehensive API documentation with OpenAPI/Swagger
- Health check endpoints for monitoring
- File storage management
- Audio format validation and processing
- User contribution tracking and statistics
- Background job monitoring with Celery
- Development and production Docker configurations
- Comprehensive test suite
- CI/CD pipeline setup
- Security features including CORS, rate limiting, and input validation

### Technical Features
- Python 3.11+ backend with FastAPI framework
- TypeScript/React frontend with Next.js
- PostgreSQL 13+ database with SQLAlchemy ORM
- Redis for caching and message queuing
- Celery for background task processing
- Docker containerization for easy deployment
- Alembic for database migrations
- Pytest for comprehensive testing
- GitHub Actions for CI/CD
- OpenAPI/Swagger documentation
- Structured logging with configurable levels
- Health monitoring and metrics collection
- File upload with validation and security checks
- JWT-based authentication
- Role-based authorization
- CORS configuration for cross-origin requests

### Documentation
- Complete setup and installation guides
- Docker deployment instructions
- Local development environment setup
- API reference documentation
- Architecture overview and system design
- Contributing guidelines and code of conduct
- Troubleshooting guides and FAQ
- System flow diagrams and documentation

---

## Release Notes

### Version 1.0.0 - Initial Release

This is the first stable release of Shrutik, a comprehensive voice data collection platform designed to help communities build high-quality voice datasets in their native languages.

**Key Highlights:**
- Complete voice data collection workflow
- Multi-user transcription with consensus system
- Admin dashboard for platform management
- Docker-based deployment for easy setup
- Comprehensive API for integration
- Modern web interface with responsive design
- Multi-language support with extensible architecture

**Getting Started:**
- Follow our [Quick Start Guide](docs/getting-started.md)
- Try the [Docker Setup](docs/docker-local-setup.md) for fastest deployment
- Read the [Contributing Guide](docs/contributing.md) to get involved

**Community:**
- Join our [Discord server](https://discord.gg/9hZ9eW8ARk)
- Report issues on [GitHub](https://github.com/Onuronon-lab/Shrutik/issues)
- Contribute to the project on [GitHub](https://github.com/Onuronon-lab/Shrutik)

Thank you to all contributors who made this release possible! 🎉

---

## Contributing to the Changelog

When contributing to Shrutik, please update this changelog with your changes:

1. Add your changes under the `[Unreleased]` section
2. Use the categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
3. Write clear, concise descriptions
4. Include relevant issue/PR numbers when applicable
5. Follow the existing format and style

Example:
```markdown
### Added
- New feature for audio transcription validation (#123)
- Support for additional audio formats (.ogg, .aac) (#124)

### Fixed
- Fixed memory leak in audio processing pipeline (#125)
- Resolved database connection timeout issues (#126)
```