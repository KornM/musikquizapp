# Optional Audio and Question Visibility Features

## Overview
Implemented two new features:
1. **Optional Audio Mode** - Admin can choose if quiz requires audio files or is text-only
2. **Question Visibility Control** - Questions are hidden from participants until admin starts the round

## Feature 1: Optional Audio Mode

### Backend Changes

#### 1. Create Quiz Lambda (`lambda/create_quiz/handler.py`)
- Added `requiresAudio` field to session creation
- Defaults to `true` for backward compatibility
- Stored in QuizSessions DynamoDB table

**Session structure:**
```json
{
  "sessionId": "uuid",
  "title": "Quiz Title",
  "description": "Description",
  "requiresAudio": true,
  "roundCount": 0,
  "status": "draft",
  "createdAt": "timestamp",
  "createdBy": "admin_id"
}
```

#### 2. Add Round Lambda (`lambda/add_round/handler.py`)
- Checks session's `requiresAudio` setting
- Only requires `audioKey` if session requires audio
- `audioKey` is optional for text-only quizzes
- Audio field only added to round if provided

### Frontend Changes

#### 1. Session Form Dialog (`frontend/src/components/admin/SessionFormDialog.vue`)
- Added toggle switch for "Requires Audio"
- Defaults to enabled (true)
- Hint text explains the purpose
- Value sent to backend when creating session

#### 2. Round Form Dialog (`frontend/src/components/admin/RoundFormDialog.vue`)
- Added `requiresAudio` prop
- Audio upload component only shown if `requiresAudio` is true
- Submit button only requires audio if session requires it
- Allows creating rounds without audio for text-only quizzes

#### 3. Session Detail View (`frontend/src/views/admin/SessionDetailView.vue`)
- Passes `requiresAudio` prop to RoundFormDialog
- Reads from session data

#### 4. Presentation View (`frontend/src/views/admin/PresentationView.vue`)
- Audio player only shown if `session.requiresAudio !== false`
- Question always visible to admin
- Cleaner interface for text-only quizzes

## Feature 2: Question Visibility Control

### How It Works

1. **Before Round Starts:**
   - Admin can see the question in presentation view
   - Participants see "waiting for round" message
   - Question is NOT visible to participants

2. **When Admin Starts Round:**
   - Admin clicks "Start Round for Participants"
   - Backend sets `currentRound` and `roundStartedAt` timestamp
   - Question becomes visible to participants
   - Participants can now submit answers

3. **Participant View Logic:**
   - Checks if `session.roundStartedAt` exists
   - Only shows question and answer form if round has started
   - Prevents participants from seeing questions before admin is ready

### Backend Changes

#### Start Round Lambda (`lambda/start_round/handler.py`)
- Already sets `roundStartedAt` timestamp when round starts
- No changes needed - existing functionality supports this feature

### Frontend Changes

#### Participant Quiz View (`frontend/src/views/participant/QuizView.vue`)
- Added `roundStarted` reactive variable
- Checks for `session.roundStartedAt` to determine if round has started
- Question and answer form only shown when `roundStarted` is true
- Shows waiting message when round exists but hasn't started yet

**Logic:**
```javascript
// Check if round has been started (has roundStartedAt timestamp)
const isRoundStarted = !!session.value.roundStartedAt;
roundStarted.value = isRoundStarted;
```

## User Experience

### Creating a Music Quiz (with audio):
1. Admin creates session with "Requires Audio" enabled
2. Admin adds rounds with audio files
3. Admin presents quiz
4. Admin starts each round when ready
5. Participants see question only after round starts

### Creating a Text-Only Quiz (no audio):
1. Admin creates session with "Requires Audio" disabled
2. Admin adds rounds with just questions and answers (no audio upload)
3. Admin presents quiz (no audio player shown)
4. Admin starts each round when ready
5. Participants see question only after round starts

### Participant Experience:
1. Participant registers and waits
2. Sees "waiting for round" message
3. When admin starts round:
   - Question appears
   - Answer options appear
   - Can submit answer
4. Question remains hidden until admin explicitly starts the round

## Benefits

### Optional Audio:
- ✅ Flexibility for different quiz types
- ✅ Faster round creation for text-only quizzes
- ✅ No need to upload dummy audio files
- ✅ Cleaner UI when audio isn't needed

### Question Visibility Control:
- ✅ Admin controls when participants see questions
- ✅ Prevents participants from reading ahead
- ✅ Better pacing control for quiz master
- ✅ More engaging live quiz experience
- ✅ Admin can prepare/explain before revealing question

## Database Schema Updates

### QuizSessions Table:
```
- sessionId (String, Primary Key)
- title (String)
- description (String)
- requiresAudio (Boolean) ← NEW FIELD
- currentRound (Number)
- roundStartedAt (String) ← Used for visibility control
- roundCount (Number)
- status (String)
- createdAt (String)
- createdBy (String)
```

### QuizRounds Table:
```
- roundId (String, Primary Key)
- sessionId (String, Sort Key)
- question (String)
- audioKey (String) ← Now optional
- answers (List)
- correctAnswer (Number)
- roundNumber (Number)
- createdAt (String)
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

## Testing

### Test Optional Audio:
1. Create a new session with "Requires Audio" disabled
2. Add a round - verify audio upload is not shown
3. Add round with just question and answers
4. Present the quiz - verify no audio player shown
5. Verify round works correctly without audio

### Test Question Visibility:
1. Create a session and add rounds
2. Start presentation mode
3. Navigate to a round (don't start it yet)
4. Open participant view - verify question is NOT visible
5. Click "Start Round for Participants" in admin view
6. Check participant view - verify question NOW appears
7. Verify participant can submit answer

## Backward Compatibility

- Existing sessions without `requiresAudio` field default to `true`
- Existing rounds with audio continue to work
- No migration needed for existing data
