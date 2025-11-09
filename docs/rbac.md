# Role-Based Access Control (RBAC)

## Overview

Shrutik implements a comprehensive Role-Based Access Control (RBAC) system to manage user permissions and ensure secure access to platform features. The system uses three distinct roles, each with specific permissions tailored to their responsibilities.

## User Roles

### 1. Contributor (Default Role)

**Description:** Regular users who contribute voice recordings and transcriptions to the platform.

**Permissions:**
- ✅ `record_voice` - Record and upload voice samples
- ✅ `transcribe_audio` - Transcribe audio chunks
- ✅ `view_own_data` - View their own recordings and transcriptions

**Access:**
- Can create recording sessions
- Can upload voice recordings
- Can transcribe assigned audio chunks
- Can view their own contribution statistics
- Can view their own recordings and transcriptions
- **Cannot** access other users' data
- **Cannot** manage users or system settings
- **Cannot** export data
- **Cannot** access admin features

**Use Case:** Community members contributing to voice data collection.

---

### 2. Admin (Highest Authority)

**Description:** Platform administrators with full management authority over users, content, and system operations.

**Permissions:**
- ✅ `record_voice` - Record and upload voice samples
- ✅ `transcribe_audio` - Transcribe audio chunks
- ✅ `view_own_data` - View their own recordings and transcriptions
- ✅ `manage_users` - **Create, update, and manage user accounts** (Admin only)
- ✅ `manage_scripts` - **Create and manage recording scripts** (Admin only)
- ✅ `view_all_data` - View all users' recordings and transcriptions
- ✅ `quality_review` - Review and validate transcription quality
- ✅ `view_statistics` - Access platform-wide statistics and analytics
- ✅ `export_data` - Export validated datasets and metadata

**Access:**
- All Contributor permissions
- **User management** (create, update, delete users, assign roles)
- **Script management** (create, update, delete scripts)
- View all recordings and transcriptions across all users
- Quality review and validation
- Platform statistics and analytics
- Data export functionality
- Admin dashboard
- System monitoring and configuration
- **Cannot** access raw system data or advanced developer tools

**Use Case:** Platform administrators managing the community, users, and content.

---

### 3. Sworik Developer (Research & Development)

**Description:** Research and development team members focused on data science, model training, and technical development. They have data access but **not** administrative privileges.

**Permissions:**
- ✅ `record_voice` - Record and upload voice samples
- ✅ `transcribe_audio` - Transcribe audio chunks
- ✅ `view_own_data` - View their own recordings and transcriptions
- ✅ `view_all_data` - View all users' recordings and transcriptions
- ✅ `quality_review` - Review and validate transcription quality
- ✅ `view_statistics` - Access platform-wide statistics and analytics
- ✅ `export_data` - Export validated datasets and metadata
- ✅ `access_raw_data` - Access raw system data and advanced tools
- ❌ `manage_users` - **Cannot manage users** (Admin only)
- ❌ `manage_scripts` - **Cannot manage scripts** (Admin only)

**Access:**
- All Contributor permissions
- View all recordings and transcriptions for research
- Quality review and validation
- Platform statistics and analytics
- Data export for research and model training
- Raw data access for development
- Advanced debugging tools
- API development and testing tools
- **Cannot** manage users or assign roles
- **Cannot** manage scripts or system configuration

**Use Case:** Data scientists, ML engineers, and core developers working on voice technology research.

---

## Permission Matrix

| Permission | Contributor | Admin | Sworik Developer |
|------------|-------------|-------|------------------|
| `record_voice` | ✅ | ✅ | ✅ |
| `transcribe_audio` | ✅ | ✅ | ✅ |
| `view_own_data` | ✅ | ✅ | ✅ |
| `manage_users` | ❌ | ✅ | ❌ |
| `manage_scripts` | ❌ | ✅ | ❌ |
| `view_all_data` | ❌ | ✅ | ✅ |
| `quality_review` | ❌ | ✅ | ✅ |
| `view_statistics` | ❌ | ✅ | ✅ |
| `export_data` | ❌ | ✅ | ✅ |
| `access_raw_data` | ❌ | ❌ | ✅ |

## API Endpoint Access

### Public Endpoints (No Authentication Required)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /` - API root
- `GET /health` - Health check
- `GET /docs` - API documentation

### Contributor Endpoints
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/me/stats` - Get user statistics
- `POST /api/recordings/sessions` - Create recording session
- `POST /api/recordings/upload` - Upload recording
- `GET /api/recordings/` - Get user's recordings
- `GET /api/recordings/{id}` - Get specific recording
- `DELETE /api/recordings/{id}` - Delete own recording
- `POST /api/transcriptions/` - Submit transcription
- `GET /api/transcriptions/` - Get user's transcriptions
- `GET /api/chunks/available` - Get available chunks for transcription

### Admin Endpoints
All Contributor endpoints, plus:
- `POST /api/auth/users` - Create user with role
- `PUT /api/auth/users/{id}/role` - Update user role
- `GET /api/auth/users` - List all users
- `GET /api/recordings/admin/all` - Get all recordings
- `GET /api/recordings/admin/statistics` - Get recording statistics
- `PATCH /api/recordings/{id}/status` - Update recording status
- `POST /api/recordings/admin/batch-process` - Batch process recordings
- `POST /api/recordings/admin/reprocess-failed` - Reprocess failed recordings
- `POST /api/recordings/admin/cleanup-orphaned-chunks` - Cleanup orphaned chunks
- `GET /api/transcriptions/admin/all` - Get all transcriptions
- `GET /api/transcriptions/admin/statistics` - Get transcription statistics
- `POST /api/admin/users` - Admin user management
- `GET /api/admin/statistics` - Platform statistics
- `POST /api/export/dataset` - Export dataset
- `POST /api/export/metadata` - Export metadata
- `GET /api/export/history` - View export history
- `GET /api/export/formats` - Get supported formats
- `GET /api/export/stats` - Get export statistics

### Sworik Developer Endpoints
All Contributor endpoints, plus:
- `POST /api/export/dataset` - Export dataset (shared with Admin)
- `POST /api/export/metadata` - Export metadata (shared with Admin)
- `GET /api/export/history` - View export history (shared with Admin)
- `GET /api/export/formats` - Get supported formats (shared with Admin)
- `GET /api/export/stats` - Get export statistics (shared with Admin)
- `GET /api/recordings/admin/all` - Get all recordings (shared with Admin)
- `GET /api/recordings/admin/statistics` - Get recording statistics (shared with Admin)
- `GET /api/transcriptions/admin/all` - Get all transcriptions (shared with Admin)
- `GET /api/transcriptions/admin/statistics` - Get transcription statistics (shared with Admin)
- Access to raw data endpoints
- Advanced debugging endpoints

**Note:** Sworik Developers **cannot** access user management or script management endpoints (Admin only)

## Role Assignment

### Default Role
- All new user registrations are automatically assigned the **Contributor** role
- This is enforced at the application level and cannot be bypassed

### Role Changes
Only users with **Admin** or **Sworik Developer** roles can change user roles:

**Via API:**
```bash
PUT /api/auth/users/{user_id}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "admin"
}
```

**Via Admin Dashboard:**
- Navigate to User Management
- Select user
- Change role from dropdown
- Save changes

### Creating Admin Users

**Method 1: CLI Script (Initial Setup)**
```bash
python scripts/create_admin.py --name "Admin User" --email admin@example.com --role admin
```

**Method 2: API (Requires Existing Admin)**
```bash
POST /api/auth/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "New Admin",
  "email": "admin@example.com",
  "password": "secure_password",
  "role": "admin"
}
```

## Security Considerations

### Permission Checks
- All API endpoints enforce permission checks at the route level
- Permissions are verified using JWT token claims
- Invalid or expired tokens are rejected with 401 Unauthorized
- Insufficient permissions result in 403 Forbidden

### Role Hierarchy
The system uses a **specialized permission model** (not strictly hierarchical):

**Management Hierarchy:**
- **Admin** > **Contributor**
- Admins have full management authority (users, scripts, system)

**Data Access Hierarchy:**
- **Sworik Developer** has specialized data access
- **Admin** has management + data access
- **Contributor** has own data only

**Key Principle:**
- **Admin** = Management authority (can manage users and scripts)
- **Sworik Developer** = Data authority (can access and export data for research)
- These are **complementary roles**, not hierarchical
- Role changes require Admin authentication

### Audit Logging
- All role changes are logged with timestamp and actor
- Export operations are logged for audit purposes
- Admin actions are tracked for security monitoring

## Implementation Details

### Permission Checker
The `PermissionChecker` class in `app/core/security.py` handles permission validation:

```python
from app.core.security import PermissionChecker
from app.models.user import UserRole

# Check if user has permission
has_export = PermissionChecker.has_permission(user.role, "export_data")

# Require permission (raises HTTPException if not authorized)
PermissionChecker.require_permission(user.role, "export_data")

# Require specific role
PermissionChecker.require_role(user.role, UserRole.ADMIN)
```

### Dependency Injection
FastAPI dependencies enforce permissions at the route level:

```python
from app.core.dependencies import (
    require_admin,
    require_sworik_developer,
    require_export_permission,
    get_current_active_user
)

# Require admin role
@router.get("/admin/endpoint")
async def admin_endpoint(current_user: User = Depends(require_admin)):
    pass

# Require specific permission
@router.post("/export")
async def export_data(current_user: User = Depends(require_export_permission)):
    pass

# Any authenticated user
@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    pass
```

## Best Practices

### For Developers
1. Always use dependency injection for permission checks
2. Never bypass permission checks in service layer
3. Log all permission-sensitive operations
4. Use the most restrictive permission necessary
5. Test permission boundaries thoroughly

### For Administrators
1. Follow principle of least privilege
2. Regularly audit user roles and permissions
3. Remove unnecessary admin access
4. Monitor export and admin operations
5. Use strong passwords for admin accounts

### For Contributors
1. Protect your account credentials
2. Report suspicious activity
3. Don't share your account
4. Use strong, unique passwords
5. Enable 2FA when available (future feature)

## Future Enhancements

Planned improvements to the RBAC system:

- [ ] Fine-grained permissions (per-resource permissions)
- [ ] Custom roles with configurable permissions
- [ ] Time-limited role assignments
- [ ] Multi-factor authentication for admin roles
- [ ] Permission delegation
- [ ] Role-based rate limiting
- [ ] Audit log viewer in admin dashboard
- [ ] Permission request workflow

## Troubleshooting

### "Insufficient permissions" Error
**Cause:** User doesn't have required permission for the endpoint  
**Solution:** Contact an admin to request role upgrade if needed

### "Insufficient role" Error
**Cause:** User's role doesn't match required role(s)  
**Solution:** Verify you're using the correct account or request role change

### Cannot Access Export Page
**Cause:** User doesn't have `export_data` permission  
**Solution:** Must be Admin or Sworik Developer to access export features

### Cannot Create Admin Users
**Cause:** Only admins can create users with roles  
**Solution:** Use CLI script for initial admin or contact existing admin

## Related Documentation

- [API Reference](api-reference.md) - Complete API documentation
- [Security](../SECURITY.md) - Security policies and reporting
- [Contributing](contributing.md) - Contribution guidelines
- [Architecture](architecture.md) - System architecture overview

## Questions?

If you have questions about roles and permissions:
1. Check this documentation first
2. Review the [FAQ](faq.md)
3. Ask in community discussions
4. Contact the development team

---

**Last Updated:** 2025-11-09  
**Version:** 1.0.0
