# Frequently Asked Questions

## General Questions

### What is Shrutik?

Shrutik (শ্রুতিক) is an open-source voice data collection platform designed to help communities build high-quality voice datasets in their native languages. The name "Shrutik" means "listener" in Bengali, reflecting our mission to listen to and preserve diverse voices.

### What languages does Shrutik support?

Shrutik is designed to support any language. Currently, it comes pre-configured with Bengali (Bangla), but administrators can easily add support for additional languages through the admin interface.

### Is Shrutik free to use?

Yes! Shrutik is completely free and open-source under the MIT License. You can use it, modify it, and distribute it freely.

## Technical Questions

### What are the system requirements?

**For Docker (Recommended):**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum, 8GB recommended
- 10GB free disk space

**For Local Development:**
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- 8GB RAM recommended

### Can I deploy Shrutik to production?

Yes! Shrutik is production-ready. We recommend using Docker for production deployments. See our deployment guides for detailed instructions.

### How do I backup my data?

**Database Backup:**
```bash
# Create database backup
docker-compose exec postgres pg_dump -U postgres voice_collection > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres voice_collection < backup.sql
```

**File Uploads Backup:**
```bash
# Backup uploads directory
tar -czf uploads-backup.tar.gz uploads/
```

### How do I scale Shrutik for more users?

Shrutik is designed to scale horizontally:

1. **Database**: Use PostgreSQL with read replicas
2. **Redis**: Use Redis Cluster for high availability
3. **Backend**: Run multiple backend instances behind a load balancer
4. **File Storage**: Use cloud storage (S3, MinIO) instead of local storage
5. **Background Jobs**: Scale Celery workers across multiple machines

## Usage Questions

### How do I add a new language?

1. Log in as an admin user
2. Go to the admin dashboard
3. Navigate to "Languages" section
4. Click "Add Language"
5. Enter language name and ISO code
6. Add scripts/texts for that language

### What audio formats are supported?

Shrutik supports these audio formats:
- WAV (recommended for quality)
- MP3
- M4A
- FLAC
- WebM

### What's the maximum file size for uploads?

The default maximum file size is 100MB. This can be configured in the environment variables:

```env
MAX_FILE_SIZE=104857600  # 100MB in bytes
```

### How does the transcription consensus system work?

Shrutik uses a multi-contributor consensus system:

1. Multiple users transcribe the same audio
2. The system compares transcriptions
3. When transcriptions match (or are very similar), they're marked as "consensus"
4. High-consensus transcriptions are considered high-quality data

### Can I export my data?

Yes! Administrators can export data through the admin API:

- Audio files and metadata
- Transcriptions and consensus data
- User statistics and contributions
- Quality metrics

## Development Questions

### How do I contribute to Shrutik?

1. Fork the repository on GitHub
2. Set up your development environment
3. Make your changes
4. Write tests for new features
5. Submit a pull request

See our [Contributing Guide](contributing.md) for detailed instructions.

### How do I report bugs?

1. Check if the issue already exists in [GitHub Issues](https://github.com/Onuronon-lab/Shrutik/issues)
2. If not, create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Error logs

### How do I request new features?

Create a feature request in [GitHub Issues](https://github.com/Onuronon-lab/Shrutik/issues) with:
- Clear description of the feature
- Use case and benefits
- Proposed implementation (if you have ideas)

### Can I customize the UI?

Yes! The frontend is built with Next.js and React. You can:
- Modify the existing components
- Add new pages and features
- Customize styling and themes
- Add support for new languages in the UI

## Privacy and Security

### How is user data protected?

Shrutik implements several security measures:
- Password hashing with bcrypt
- JWT token-based authentication
- Role-based access control
- Input validation and sanitization
- CORS protection
- Rate limiting

### Can I run Shrutik offline?

Yes! Shrutik can run completely offline once deployed. All processing happens locally on your infrastructure.

### How do I configure HTTPS?

For production deployments, configure HTTPS using:
- Reverse proxy (nginx, Apache)
- Load balancer with SSL termination
- Cloud provider SSL certificates

Example nginx configuration is available in our deployment guides.

## Community and Support

### Where can I get help?

1. **Documentation**: This documentation site
2. **GitHub Issues**: For bugs and feature requests
3. **Discord**: [Join our community](https://discord.gg/9hZ9eW8ARk)
4. **Email**: Contact the maintainers

### How can I stay updated?

- Watch the GitHub repository for releases
- Join our Discord community
- Follow our social media channels
- Subscribe to our newsletter (coming soon)

### Can I hire someone to help with deployment?

While Shrutik is open-source and free, you can:
- Hire freelance developers familiar with the stack
- Contact the core team for consulting services
- Engage with the community for paid support

## Troubleshooting

### The application won't start

See our detailed [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.

### I forgot my admin password

Reset your admin password:

```bash
# Using Docker
docker-compose exec backend python create_admin.py

# Local development
python create_admin.py
```

This will create a new admin user or update the existing one.

### The database is corrupted

If your database becomes corrupted:

1. Stop all services
2. Restore from backup (if available)
3. Or reset the database:

```bash
./docker-dev.sh cleanup
./docker-dev.sh start
./docker-dev.sh migrate
python create_admin.py
```

**Note**: This will delete all data!

---

## Still have questions?

If your question isn't answered here:

1. Check our [Troubleshooting Guide](troubleshooting.md)
2. Search [GitHub Issues](https://github.com/Onuronon-lab/Shrutik/issues)
3. Join our [Discord community](https://discord.gg/9hZ9eW8ARk)
4. Create a new issue on GitHub

We're here to help! 🎉