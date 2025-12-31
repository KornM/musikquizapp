# Session Activation/Deactivation Feature

## Date: December 30, 2024

## Overview

Changed the session management flow so admins can activate/deactivate sessions instead of starting individual rounds. This provides better control over when participants can join and participate.

## Changes Made

### 1. Backend - New Lambda Function

**Created: `lambda/update_session/handler.py`**
- Allows admins to update session properties
- Supports updating: status, title, description
- Validates admin permissions and tenant access
- Status options: `draft`, `active`, `completed`

### 2. Infrastructure - CDK Updates

**Updated: `cdk/music_quiz_stack/lambda_functions.py`**
- Added `UpdateSessionFunction` Lambda
- Granted read/write permissions to QuizSessions table

**Updated: `cdk/music_quiz_stack/api_gateway.py`**
- Added `PUT /admin/quiz-sessions/{sessionId}` endpoint
- Allows updating session properties including status

### 3. Frontend - API Service

**Updated: `frontend/src/services/api.js`**
- Added `updateSession(sessionId, data)` method
- Sends PUT request to update session

### 4. Frontend - Session Card Component

**Updated: `frontend/src/components/admin/SessionCard.vue`**
- Added "Activate" button (shown when status = draft)
- Added "Deactivate" button (shown when status = active)
- Added "Complete" button (shown when status = active)
- Added reactive variables: `activating`, `deactivating`
- Added methods: `activateSession()`, `deactivateSession()`
- Emits "updated" event when session status changes

### 5. Frontend - Dashboard View

**Updated: `frontend/src/views/admin/DashboardView.vue`**
- Added `@updated` event handler to SessionCard
- Added `handleSessionUpdated()` method
- Refreshes session list after status update
- Shows success message

## New Workflow

### Admin Workflow:
1. **Create Session** → Status: `draft`
2. **Add Rounds** → Still in `draft`
3. **Click "Activate"** → Status: `active`
   - Participants can now see and join the session
   - Admin can start individual rounds
4. **Click "Deactivate"** → Status: `draft`
   - Participants can no longer join
   - Session goes back to draft mode
5. **Click "Complete"** → Status: `completed`
   - Session is finished
   - No more answers accepted
   - Participants redirected to lobby

### Participant Workflow:
1. Register once per tenant
2. Browse lobby for available sessions
3. Join sessions with status = `active`
4. Participate in rounds as admin starts them
5. Get redirected to lobby when session is completed

## Status Meanings

- **draft**: Session is being prepared, not visible to participants
- **active**: Session is live, participants can join and play
- **completed**: Session is finished, no more participation allowed

## API Endpoint

```
PUT /admin/quiz-sessions/{sessionId}
Authorization: Bearer <admin_token>

Body:
{
  "status": "active" | "draft" | "completed",  // optional
  "title": "string",                            // optional
  "description": "string"                       // optional
}

Response:
{
  "message": "Session updated successfully",
  "sessionId": "uuid",
  "session": { ... }
}
```

## Deployment Required

To use this feature, you must deploy the CDK changes:

```bash
cd cdk
source venv/bin/activate
cdk deploy
```

## Benefits

1. **Better Control**: Admin can control when participants can join
2. **Clearer States**: Draft → Active → Completed flow is intuitive
3. **Flexible**: Can deactivate a session temporarily if needed
4. **Participant Experience**: Only see sessions that are ready to play

## Testing Checklist

- [ ] Create a session (should be in draft status)
- [ ] Click "Activate" (should change to active)
- [ ] Verify participants can see it in lobby
- [ ] Click "Deactivate" (should change back to draft)
- [ ] Verify participants can't see it anymore
- [ ] Click "Activate" again
- [ ] Start rounds and play
- [ ] Click "Complete" (should change to completed)
- [ ] Verify participants are redirected to lobby

---

**Status**: Ready for deployment
**Next Step**: Deploy CDK and test the flow
