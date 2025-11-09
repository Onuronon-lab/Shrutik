# RBAC Changes Summary

## Changes Made

### 1. Fixed Role Hierarchy

**Previous (Incorrect):**
- Sworik Developer had `manage_users` and `manage_scripts` permissions
- This was incorrect as developers shouldn't manage users

**Current (Correct):**
- **Admin** = Management authority (users, scripts, system)
- **Sworik Developer** = Data authority (research, export, raw data access)
- These are complementary roles, not hierarchical

### 2. Permission Updates

**Admin Role:**
- ✅ `manage_users` - Only admins can manage users
- ✅ `manage_scripts` - Only admins can manage scripts
- ✅ `export_data` - Admins can export data (NEW)
- ✅ All management permissions

**Sworik Developer Role:**
- ❌ `manage_users` - REMOVED (Admin only)
- ❌ `manage_scripts` - REMOVED (Admin only)
- ✅ `export_data` - Can export for research
- ✅ `access_raw_data` - Can access raw data for development
- ✅ Data viewing and statistics permissions

### 3. Updated Permission Matrix

| Permission | Contributor | Admin | Sworik Developer |
|------------|-------------|-------|------------------|
| `manage_users` | ❌ | ✅ | ❌ (Changed) |
| `manage_scripts` | ❌ | ✅ | ❌ (Changed) |
| `export_data` | ❌ | ✅ (NEW) | ✅ |
| `access_raw_data` | ❌ | ❌ | ✅ |

## Files Modified

1. **app/core/security.py**
   - Removed `manage_users` from SWORIK_DEVELOPER
   - Removed `manage_scripts` from SWORIK_DEVELOPER
   - Added `export_data` to ADMIN

2. **docs/rbac.md**
   - Complete RBAC documentation created
   - Updated role descriptions
   - Fixed permission matrix
   - Clarified role hierarchy
   - Added API endpoint access documentation

## Verification

### Admin Can:
- ✅ Manage users (create, update, delete, assign roles)
- ✅ Manage scripts
- ✅ Export data
- ✅ View all data
- ✅ Access admin dashboard

### Sworik Developer Can:
- ✅ Export data for research
- ✅ Access raw data
- ✅ View all data
- ✅ View statistics
- ❌ Cannot manage users
- ❌ Cannot manage scripts

### Contributor Can:
- ✅ Record voice
- ✅ Transcribe audio
- ✅ View own data
- ❌ Cannot access admin features
- ❌ Cannot export data
- ❌ Cannot manage anything

## API Endpoints Verified

### Admin-Only Endpoints (Correct):
- `POST /api/auth/users` - Create user with role
- `PUT /api/auth/users/{id}/role` - Update user role
- `PUT /api/admin/users/{id}/role` - Update user role
- `DELETE /api/admin/users/{id}` - Delete user
- `POST /api/scripts` - Create script
- `PUT /api/scripts/{id}` - Update script
- `DELETE /api/scripts/{id}` - Delete script

### Admin OR Sworik Developer Endpoints (Correct):
- `POST /api/export/dataset` - Export dataset
- `POST /api/export/metadata` - Export metadata
- `GET /api/export/history` - View export history
- `GET /api/recordings/admin/all` - View all recordings
- `GET /api/recordings/admin/statistics` - View statistics
- `GET /api/transcriptions/admin/all` - View all transcriptions
- `GET /api/system/health` - System health
- `GET /api/system/metrics` - System metrics

## Testing

To test the changes:

```bash
# Test admin can export
curl -X POST /api/export/dataset \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"format": "json"}'

# Test sworik developer can export
curl -X POST /api/export/dataset \
  -H "Authorization: Bearer <sworik_dev_token>" \
  -H "Content-Type: application/json" \
  -d '{"format": "json"}'

# Test sworik developer CANNOT manage users (should get 403)
curl -X POST /api/auth/users \
  -H "Authorization: Bearer <sworik_dev_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "test@example.com", "password": "pass", "role": "admin"}'
```

## Documentation

Complete RBAC documentation is now available at:
- `docs/rbac.md` - Comprehensive role and permission documentation

## Summary

The RBAC system now correctly implements:
- **Admin** = Management authority
- **Sworik Developer** = Data/research authority
- Clear separation of concerns
- Proper permission boundaries
- Comprehensive documentation

All changes maintain backward compatibility for existing functionality while fixing the incorrect permission assignments.
