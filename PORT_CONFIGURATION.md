# Port Configuration - Avoiding Conflicts

## Current Port Usage on Your EC2

### RustFS Manager (Already Running):
- **HTTP:** Port 80
- **HTTPS:** Port 443  
- **PostgreSQL:** Port 5432
- **Redis:** Port 6379 (internal)

### Old Shrutik (Already Running):
- **HTTP:** Port 8080
- **HTTPS:** Port 8443

## New Shrutik Configuration (No Conflicts):

### External Ports (Accessible from Internet):
- **HTTP:** Port **3080** ← Your main access port
- **HTTPS:** Port **3443** ← For future SSL setup
- **PostgreSQL:** Port **5433** ← Database access if needed

### Internal Ports (Docker network only):
- **Backend API:** Port 8000 (internal)
- **Celery Flower:** Port 5555 (internal, accessed via nginx)
- **Redis:** Port 6379 (internal)

## Access URLs

After deployment, access Shrutik at:
- **Main App:** `http://YOUR-EC2-IP:3080/`
- **API Docs:** `http://YOUR-EC2-IP:3080/api/docs`
- **Admin Panel:** `http://YOUR-EC2-IP:3080/admin/flower/`

## Security Group Rule

Add this rule to your EC2 security group:
- **Type:** Custom TCP
- **Port:** 3080
- **Source:** 0.0.0.0/0

## No Conflicts!

✅ **RustFS Manager** continues running on ports 80, 443, 5432  
✅ **Old Shrutik** continues running on ports 8080, 8443  
✅ **New Shrutik** runs on ports 3080, 3443, 5433  

All applications can run simultaneously without any port conflicts!