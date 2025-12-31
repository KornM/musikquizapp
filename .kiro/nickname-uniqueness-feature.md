# Nickname Uniqueness Feature

## Date: December 30, 2024

## Overview

Added validation to prevent duplicate nicknames within a tenant. Each participant must have a unique nickname within their tenant.

## Changes Made

### 1. Backend - Register Global Participant

**Updated: `lambda/register_global_participant/handler.py`**
- Added import for `scan` function
- Added nickname uniqueness check before registration
- Scans GlobalParticipants table for existing participants with same name in tenant
- Returns 409 Conflict error if nickname is already taken
- Trims whitespace from names for comparison
- Continues registration if scan fails (graceful degradation)

### 2. Backend - Update Global Participant

**Updated: `lambda/update_global_participant/handler.py`**
- Added import for `scan` function
- Added nickname uniqueness check when updating name
- Only checks if name is actually being changed
- Excludes current participant from duplicate check
- Returns 409 Conflict error if nickname is already taken
- Continues update if scan fails (graceful degradation)

### 3. Frontend - Registration View

**Updated: `frontend/src/views/participant/RegisterView.vue`**
- Added error handling for 409 Conflict status
- Shows user-friendly message: "This nickname is already taken. Please choose a different name."
- Clears previous errors before attempting registration
- Better error logging for debugging

## How It Works

### Registration Flow:
1. User enters nickname and selects avatar
2. Frontend sends registration request
3. Backend checks if nickname exists in tenant
4. If nickname exists → Returns 409 error with message
5. If nickname is unique → Creates participant
6. Frontend shows error or redirects to lobby

### Update Flow:
1. User updates their nickname
2. Frontend sends update request
3. Backend checks if new nickname exists (excluding current user)
4. If nickname exists → Returns 409 error with message
5. If nickname is unique → Updates participant
6. Frontend shows error or confirms update

## Error Response

```json
{
  "error": {
    "code": "NICKNAME_TAKEN",
    "message": "The nickname 'John' is already taken. Please choose a different name."
  }
}
```

## Benefits

1. **No Confusion**: Each participant has a unique identifier
2. **Better UX**: Clear error messages guide users to choose different names
3. **Tenant Isolation**: Nicknames only need to be unique within a tenant
4. **Graceful Degradation**: If check fails, registration still proceeds

## Scope

- **Uniqueness Level**: Per tenant (not global)
- **Case Sensitivity**: Case-sensitive comparison
- **Whitespace**: Trimmed before comparison
- **Special Characters**: Allowed in nicknames

## Testing Checklist

- [ ] Register with new nickname (should succeed)
- [ ] Register with existing nickname (should fail with 409)
- [ ] Update to new nickname (should succeed)
- [ ] Update to existing nickname (should fail with 409)
- [ ] Update to same nickname (should succeed - no change)
- [ ] Register with whitespace around name (should trim and check)
- [ ] Different tenants can use same nickname (should succeed)

## Deployment

No CDK changes required. Just deploy the Lambda functions:

```bash
cd cdk
source venv/bin/activate
cdk deploy
```

---

**Status**: Ready for deployment
**Impact**: Improves user experience and prevents confusion
