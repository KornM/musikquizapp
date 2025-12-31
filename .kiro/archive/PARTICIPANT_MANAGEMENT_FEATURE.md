# Participant Management Feature (CRUD)

## Overview
Adding admin interface to manage registered participants for quiz sessions. Admins can view, edit, and delete individual participants.

## Implementation Status
✅ **Complete**

### Completed
- ✅ Created `get_participants` Lambda
- ✅ Created `update_participant` Lambda  
- ✅ Created `delete_participant` Lambda
- ✅ Added Lambdas to CDK configuration
- ✅ Added API Gateway endpoints
- ✅ Created frontend API methods
- ✅ Created ParticipantManagement component
- ✅ Added to SessionDetailView
- ✅ Ready for testing

## Backend Lambdas

### 1. Get Participants
**Endpoint**: `GET /admin/quiz-sessions/{sessionId}/participants`
**Purpose**: List all participants for a session
**Response**:
```json
{
  "participants": [
    {
      "participantId": "uuid",
      "sessionId": "uuid",
      "name": "Alice",
      "avatar": "😀",
      "totalPoints": 50,
      "correctAnswers": 5,
      "createdAt": "timestamp"
    }
  ]
}
```

### 2. Update Participant
**Endpoint**: `PUT /admin/quiz-sessions/{sessionId}/participants/{participantId}`
**Purpose**: Update participant name and avatar
**Request**:
```json
{
  "name": "New Name",
  "avatar": "😎"
}
```

### 3. Delete Participant
**Endpoint**: `DELETE /admin/quiz-sessions/{sessionId}/participants/{participantId}`
**Purpose**: Delete participant and their answers
**Response**:
```json
{
  "message": "Participant deleted successfully",
  "participantId": "uuid",
  "deletedAnswers": 5
}
```

## Frontend Components

### ParticipantManagement Component
Features:
- List all participants with avatar, name, points
- Edit button for each participant
- Delete button for each participant
- Confirmation dialog for delete
- Edit dialog with name and avatar fields
- Real-time updates

### Integration
- Add tab or section in SessionDetailView
- Show participant count
- Quick actions: Edit, Delete
- Bulk actions: Clear all (existing)

## User Stories

### Admin Views Participants
1. Admin opens session detail page
2. Clicks "Participants" tab
3. Sees list of all registered participants
4. Views name, avatar, points, correct answers

### Admin Edits Participant
1. Admin clicks edit button on participant
2. Dialog opens with current name and avatar
3. Admin changes name or avatar
4. Clicks save
5. Participant updated in list

### Admin Deletes Participant
1. Admin clicks delete button on participant
2. Confirmation dialog appears
3. Admin confirms deletion
4. Participant and their answers removed
5. List updates

## API Endpoints Summary

```
GET    /admin/quiz-sessions/{sessionId}/participants              → List
PUT    /admin/quiz-sessions/{sessionId}/participants/{participantId}  → Update
DELETE /admin/quiz-sessions/{sessionId}/participants/{participantId}  → Delete
DELETE /admin/quiz-sessions/{sessionId}/participants              → Clear all (existing)
```

## Deployment

```bash
# Deploy backend
cd cdk
cdk deploy

# Build and deploy frontend
cd ../frontend
npm run build
../scripts/deploy-frontend.sh
```

## Usage

1. **View Participants**: Open session detail page, scroll to "Participants" section
2. **Edit Participant**: Click pencil icon, modify name/avatar, click Save
3. **Delete Participant**: Click delete icon, confirm deletion
4. **Clear All**: Click "Clear All" button, confirm to remove all participants

## Features

- 📋 **List View** - See all participants with avatar, name, points, correct answers
- ✏️ **Edit** - Update participant name and avatar
- 🗑️ **Delete** - Remove individual participant and their answers
- 🧹 **Clear All** - Remove all participants at once
- 🏆 **Ranking** - Participants sorted by points (highest first)
- 🥇 **Leader Highlight** - Top participant highlighted in yellow

## Benefits

✅ **Better Control** - Admins can manage participants
✅ **Fix Mistakes** - Edit typos in names
✅ **Remove Duplicates** - Delete duplicate registrations
✅ **Clean Data** - Remove test participants
✅ **Flexibility** - Change avatars if needed
