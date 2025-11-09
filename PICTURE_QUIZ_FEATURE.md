# Picture Quiz Feature Implementation

## Overview
Added support for picture-based quizzes in addition to music quizzes and text-only quizzes. Admins can now choose between three quiz types when creating a session:
- **Text Only** - No media files
- **Music Quiz** - Audio files
- **Picture Quiz** - Image files

## Changes Made

### Backend Changes

#### 1. Create Quiz Lambda (`lambda/create_quiz/handler.py`)
- Changed `requiresAudio` (boolean) to `mediaType` (string enum)
- Valid values: `"none"`, `"audio"`, `"image"`
- Defaults to `"audio"` for backward compatibility
- Added validation for media type

#### 2. Add Round Lambda (`lambda/add_round/handler.py`)
- Added support for `imageKey` field
- Validates required media based on session's `mediaType`
- Audio quiz requires `audioKey`
- Picture quiz requires `imageKey`
- Text-only quiz requires neither

#### 3. Upload Image Lambda (`lambda/upload_image/handler.py`)
- New Lambda function for image uploads
- Supports JPG, PNG, GIF, WEBP formats
- Max file size: 5MB
- Stores images in S3 at: `sessions/{sessionId}/images/{uuid}.{ext}`
- Returns `imageKey` for storage in rounds table

#### 4. Lambda Functions CDK (`cdk/music_quiz_stack/lambda_functions.py`)
- Added `upload_image` Lambda function
- Configured with same permissions as `upload_audio`
- Uses shared audio bucket for all media

#### 5. API Gateway (`cdk/music_quiz_stack/api_gateway.py`)
- Added `POST /admin/image` endpoint
- Routes to `upload_image` Lambda function

### Frontend Changes

#### 1. Session Form Dialog (`frontend/src/components/admin/SessionFormDialog.vue`)
- Replaced "Requires Audio" toggle with "Quiz Type" dropdown
- Three options:
  - Text Only - No media files
  - Music Quiz - Audio files  
  - Picture Quiz - Image files
- Sends `mediaType` to backend

#### 2. Image Upload Component (`frontend/src/components/admin/ImageUpload.vue`)
- New component for image uploads
- Drag-and-drop support
- Image preview after upload
- Validates file type and size
- Shows upload progress and success/error messages

#### 3. Round Form Dialog (`frontend/src/components/admin/RoundFormDialog.vue`)
- Changed `requiresAudio` prop to `mediaType` prop
- Conditionally shows:
  - `AudioUpload` component if `mediaType === 'audio'`
  - `ImageUpload` component if `mediaType === 'image'`
  - Neither if `mediaType === 'none'`
- Handles both `audioKey` and `imageKey` in round data
- Submit button disabled until required media is uploaded

#### 4. Session Detail View (`frontend/src/views/admin/SessionDetailView.vue`)
- Passes `mediaType` to `RoundFormDialog` components
- Reads from session data

#### 5. Presentation View (`frontend/src/views/admin/PresentationView.vue`)
- Added `currentImageUrl` state
- Added `loadImage()` function
- Added `loadMedia()` function that calls appropriate loader
- Conditionally displays:
  - Audio player if `mediaType === 'audio'`
  - Image display if `mediaType === 'image'`
  - Neither if `mediaType === 'none'`
- Image displayed with max-height of 400px

#### 6. API Service (`frontend/src/services/api.js`)
- Added `uploadImage()` method
- Converts image to base64 and posts to `/admin/image`
- Returns `imageKey` on success

#### 7. Sessions Store (`frontend/src/stores/sessions.js`)
- Added `uploadImage()` action
- Handles image upload with error handling

## Database Schema Updates

### QuizSessions Table
```
- sessionId (String, Primary Key)
- title (String)
- description (String)
- mediaType (String) ← NEW FIELD (replaces requiresAudio)
  - Values: "none", "audio", "image"
- currentRound (Number)
- roundStartedAt (String)
- roundCount (Number)
- status (String)
- createdAt (String)
- createdBy (String)
```

### QuizRounds Table
```
- roundId (String, Primary Key)
- sessionId (String, Sort Key)
- question (String)
- audioKey (String) ← Optional
- imageKey (String) ← NEW FIELD, Optional
- answers (List)
- correctAnswer (Number)
- roundNumber (Number)
- createdAt (String)
```

## S3 Storage Structure

```
sessions/
  {sessionId}/
    audio/
      {uuid}.mp3
      {uuid}.wav
    images/
      {uuid}.jpg
      {uuid}.png
      {uuid}.gif
      {uuid}.webp
```

## User Flows

### Creating a Picture Quiz
1. Admin clicks "Create New Session"
2. Enters title and description
3. Selects "Picture Quiz - Image files" from dropdown
4. Creates session
5. Adds rounds:
   - Enters question
   - Uploads image (drag-drop or browse)
   - Enters 4 answer options
   - Selects correct answer
6. Presents quiz - image is displayed to admin
7. Starts round - image becomes visible to participants

### Creating a Music Quiz
1. Same as before
2. Select "Music Quiz - Audio files"
3. Upload audio files for each round

### Creating a Text-Only Quiz
1. Same as before
2. Select "Text Only - No media files"
3. No media upload required

## API Endpoints

### New Endpoint
```
POST /admin/image
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
  "imageData": "base64_encoded_image",
  "fileName": "picture.jpg",
  "sessionId": "uuid"
}

Response:
{
  "imageKey": "sessions/{sessionId}/images/{uuid}.jpg",
  "url": "presigned_url"
}
```

### Modified Endpoints
```
POST /admin/quiz-sessions
Body:
{
  "title": "Quiz Title",
  "description": "Description",
  "mediaType": "image"  // "none", "audio", or "image"
}

POST /admin/quiz-sessions/{sessionId}/rounds
Body:
{
  "question": "What movie is this from?",
  "imageKey": "sessions/.../images/....jpg",  // or audioKey
  "answers": ["A", "B", "C", "D"],
  "correctAnswer": 0
}
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

## Benefits

✅ **Versatility** - Support for multiple quiz types
✅ **Flexibility** - Choose appropriate media for content
✅ **Reusability** - Same infrastructure for all media types
✅ **User Experience** - Clear UI for each quiz type
✅ **Performance** - CloudFront delivery for all media
✅ **Scalability** - Easy to add more media types in future

## Future Enhancements

Potential additions:
- Video support
- Multiple images per round
- Audio + Image combination
- PDF/Document support
- Image cropping/editing tools
- Bulk image upload

## Testing Checklist

- [ ] Create text-only quiz
- [ ] Create music quiz with audio files
- [ ] Create picture quiz with images
- [ ] Upload various image formats (JPG, PNG, GIF, WEBP)
- [ ] Test image size validation (max 5MB)
- [ ] Test drag-and-drop image upload
- [ ] Verify image display in presentation view
- [ ] Verify image display to participants after round starts
- [ ] Test round navigation with images
- [ ] Verify CloudFront URL generation for images
- [ ] Test backward compatibility with existing sessions

## Backward Compatibility

- Existing sessions without `mediaType` default to `"audio"`
- Existing sessions with `requiresAudio: true` work as audio quizzes
- Existing sessions with `requiresAudio: false` work as text-only quizzes
- No data migration required
