# Frontend Export Access Fix

## Problem
Admin users couldn't access the Export Data page because:
1. The route was restricted to `sworik_developer` only
2. The navigation link was only visible to `sworik_developer`

## Solution
Updated frontend to allow both `admin` and `sworik_developer` roles to access export functionality.

## Changes Made

### 1. Updated ProtectedRoute Component
**File:** `frontend/src/components/auth/ProtectedRoute.tsx`

**Before:**
```typescript
interface ProtectedRouteProps {
  requiredRole?: 'contributor' | 'admin' | 'sworik_developer';
}

if (requiredRole && user?.role !== requiredRole) {
  return <Navigate to="/unauthorized" replace />;
}
```

**After:**
```typescript
interface ProtectedRouteProps {
  requiredRole?: 'contributor' | 'admin' | 'sworik_developer' | ('admin' | 'sworik_developer')[];
}

if (requiredRole) {
  const allowedRoles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
  if (!user?.role || !allowedRoles.includes(user.role as any)) {
    return <Navigate to="/unauthorized" replace />;
  }
}
```

**Change:** Now supports both single role and array of roles.

### 2. Updated Export Route
**File:** `frontend/src/App.tsx`

**Before:**
```typescript
<Route path="/export" element={
  <ProtectedRoute requiredRole="sworik_developer">
    <ExportPage />
  </ProtectedRoute>
} />
```

**After:**
```typescript
<Route path="/export" element={
  <ProtectedRoute requiredRole={['admin', 'sworik_developer']}>
    <ExportPage />
  </ProtectedRoute>
} />
```

**Change:** Export page now accessible to both admin and sworik_developer.

### 3. Updated Navigation Menu
**File:** `frontend/src/components/layout/Navbar.tsx`

**Before:**
```typescript
{
  name: 'Export Data',
  href: '/export',
  icon: ArrowDownTrayIcon,
  roles: ['sworik_developer'],
},
```

**After:**
```typescript
{
  name: 'Export Data',
  href: '/export',
  icon: ArrowDownTrayIcon,
  roles: ['admin', 'sworik_developer'],
},
```

**Change:** Export Data link now visible to both admin and sworik_developer.

## How Admins Access Export

### Via Navigation Menu
1. Login as Admin
2. Click "Export Data" in the navigation menu
3. Access the export page with full functionality

### Via Direct URL
1. Login as Admin
2. Navigate to `/export`
3. Access granted (no longer redirected to unauthorized)

## Testing

### Test Admin Access
```bash
# 1. Login as admin
# 2. Check navigation menu - "Export Data" link should be visible
# 3. Click "Export Data" or navigate to /export
# 4. Should see export page (not unauthorized page)
```

### Test Sworik Developer Access
```bash
# 1. Login as sworik_developer
# 2. Check navigation menu - "Export Data" link should be visible
# 3. Click "Export Data" or navigate to /export
# 4. Should see export page (not unauthorized page)
```

### Test Contributor Access
```bash
# 1. Login as contributor
# 2. Check navigation menu - "Export Data" link should NOT be visible
# 3. Try to navigate to /export directly
# 4. Should be redirected to unauthorized page
```

## Backend Verification

The backend already supports admin export access:
- ✅ `POST /api/export/dataset` - Uses `require_export_permission`
- ✅ `POST /api/export/metadata` - Uses `require_export_permission`
- ✅ `GET /api/export/history` - Uses `require_export_permission`
- ✅ Admin role has `export_data` permission (added in RBAC fix)

## Files Modified

1. `frontend/src/components/auth/ProtectedRoute.tsx` - Support multiple roles
2. `frontend/src/App.tsx` - Allow admin + sworik_developer for export route
3. `frontend/src/components/layout/Navbar.tsx` - Show export link to admin + sworik_developer

## Summary

**Before:**
- Only Sworik Developers could access export page
- Admins were blocked despite having backend permission

**After:**
- Both Admins and Sworik Developers can access export page
- Navigation link visible to both roles
- Route protection allows both roles
- Backend permissions already support this

The fix is complete and admins can now export data! 🎉
