# Shrutik — dev-testing

This branch is used for **development, experiments, and testing** before changes are promoted to stable branches.

### Purpose

- Test new features and ideas
- Validate bug fixes
- Run integration & load tests
- Break things safely (on purpose)

### Stability

⚠️ **Not stable. Not production-ready.**  
Expect frequent changes, unfinished features, and occasional chaos.

### Usage

- For contributors and internal testing only
- Do **not** deploy this branch to production
- If you want something reliable, switch branches

### Notes

- May contain temporary configs
- APIs and behavior can change without notice
- Force pushes may happen

## Docker Troubleshooting

### Export Batches Disappear After Container Restart

**Problem**: Export batches work when containers are running, but show "500 Internal Server Error" or "doesn't exist" after running `docker compose down` and restarting.

**Cause**: Export files are stored in `/app/exports` inside the container, which gets destroyed when containers are stopped.

**Solution**: The docker-compose.yml now includes proper volume mappings to persist export data:

```yaml
volumes:
  - ./exports:/app/exports # Persists export batches
  - ./uploads:/app/uploads # Persists uploaded files
```

**Quick Fix**:

1. Run the volume checker: `python scripts/check_docker_volumes.py`
2. Restart containers: `docker compose down && docker compose up -d --build`

**Prevention**: Always ensure the `exports/` directory exists on your host system and is properly mounted as a volume.

---

Built fast. Tested hard. Shipped only when ready 🚀
