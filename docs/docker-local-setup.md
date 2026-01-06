# Docker Local Setup Guide

This guide explains how to run Shrutik completely with Docker on your local machine, including all the configuration changes needed to switch from local development to Docker.


# **Quick Docker Setup**

### **Prerequisites**

-   Docker 20.10+
    
-   Docker Compose 2.0+
    
-   Git
    

## **1. Clone the Repo**

```bash
git clone https://github.com/Onuronon-lab/Shrutik.git
cd Shrutik

# Switch to the deployment-dev branch
git fetch origin
git switch deployment-dev

```

## **2. Configure Environment for Docker**

Use the Docker-specific environment file:

```bash
cp .env.example .env

# Update DB host for Docker
sed -i 's@localhost:5432@postgres:5432@g' .env

```
**Available Environment Files:**
- `.env.example` - Template with all available options


## **3. Configure Frontend**

```bash
cp .env.example .env

```

## **4. Start All Containers**

Use this when running the app for the first time or after changing Dockerfiles, `requirements.txt`, or `package.json`:

```bash
docker compose up -d --build

```
### **Regular use (no changes)**

For normal daily use, when the images are already built:
```
docker compose up -d

```

Check service status:

```bash
docker compose ps

```

## **5. Initialize the Database**

Run migrations manually:

```bash
docker compose exec backend alembic upgrade head

```

Create admin user:

```bash
docker compose exec backend python scripts/create_admin.py --name "Admin" --email admin@example.com

```

## **6. Access the Application**

-   **Frontend** → [http://localhost:3000](http://localhost:3000)
    
    
-   **API Docs** → [http://localhost:8000/docs](http://localhost:8000/docs)
    
-   **Health Check** → [http://localhost:8000/health](http://localhost:8000/health)

## Configuration Changes Explained

### Key Differences: Local vs Docker

| Component | Local Development | Docker |
|-----------|------------------|---------|
| **Database URL** | `localhost:5432` | `postgres:5432` |
| **Redis URL** | `localhost:6379` | `redis:6379` |
| **Frontend API URL** | `http://localhost:8000` | `http://localhost:8000` |
| **File Paths** | `./uploads` | `/app/uploads` |




# **Development Workflow**

### Start services

```bash
docker compose up -d

```

### Stop everything

```bash
docker compose down

```

### Stop AND remove volumes (fresh reset)

```bash
docker compose down -v

```

### View logs

```bash
docker compose logs -f

```

Specific service logs:

```bash
docker compose logs -f backend

```

### Rebuild after changing requirements

```bash
docker compose build --no-cache
docker compose up -d

```

### Shell into a container

```bash
docker compose exec backend bash

```

### Check backend health

```bash
curl http://localhost:8000/health
```

# **Database Management**

Run migrations:

```bash
docker compose exec backend alembic upgrade head

```

Auto-generate migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "message"

```

Connect to PostgreSQL:

```bash
docker compose exec postgres psql -U postgres -d voice_collection

```

# **Redis Debugging**

Test Redis:

```bash
docker compose exec redis redis-cli ping

```

Restart Redis:

```bash
docker compose restart redis

```

# **Troubleshooting**

### **Port in use**

Check:

```bash
sudo lsof -i :6379
sudo lsof -i :5432

```

Kill process:

```bash
sudo kill <pid>

```

### **Backend not starting**

```bash
docker compose logs backend

```

### **Frontend not loading**

```bash
docker compose logs frontend
docker compose build frontend --no-cache
docker compose up -d frontend

``````

