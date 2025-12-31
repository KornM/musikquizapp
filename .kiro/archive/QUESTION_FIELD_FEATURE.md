# Question Field Feature

## Overview
Added a question field to each quiz round that admins can set when creating or editing rounds. The question is displayed to both the admin during presentation and to participants during the quiz.

## Changes Made

### 1. Backend - Lambda Function (`lambda/add_round/handler.py`)

**Added question field to round data:**
- Added `question` to expected input parameters
- Added validation to ensure question is required
- Stored question in the round item in DynamoDB

**Example round data:**
```json
{
  "roundId": "uuid",
  "sessionId": "uuid",
  "question": "What is the name of this song?",
  "audioKey": "sessions/.../audio/....mp3",
  "answers": ["Answer A", "Answer B", "Answer C", "Answer D"],
  "correctAnswer": 0,
  "roundNumber": 1,
  "createdAt": "1234567890"
}
```

### 2. Frontend - Round Form (`frontend/src/components/admin/RoundFormDialog.vue`)

**Added question input field:**
- Added text field for question at the top of the form
- Made question a required field
- Question is included when creating or editing rounds
- Question is populated when editing existing rounds

**Form structure:**
1. Question (text field)
2. Audio upload
3. Four answer options
4. Correct answer selection

### 3. Admin Presentation View (`frontend/src/views/admin/PresentationView.vue`)

**Display question during presentation:**
- Added a card above the audio player showing the question
- Question is displayed in large, bold text (text-h4)
- Helps admin present the quiz clearly to participants

### 4. Participant Quiz View (`frontend/src/views/participant/QuizView.vue`)

**Display question to participants:**
- Added info alert showing the question above the answer options
- Question is clearly visible when participants are answering
- Helps participants understand what they're answering

## User Experience

### Admin Flow:
1. Admin creates/edits a round
2. Enters a question (e.g., "What is the name of this song?")
3. Uploads audio file
4. Enters four answer options
5. Selects correct answer
6. During presentation, question is displayed prominently

### Participant Flow:
1. Participant sees the question in a blue info box
2. Listens to the audio (if available)
3. Reads the question to understand what to answer
4. Selects their answer from the options
5. Submits answer

## Example Questions

Common question types for music quizzes:
- "What is the name of this song?"
- "Who is the artist?"
- "What year was this song released?"
- "What album is this song from?"
- "What genre is this song?"
- "Complete the lyrics: ..."

## Deployment

```bash
cd cdk
cdk deploy
```

This will update the Lambda function to handle the question field. Existing rounds without questions will need to be edited to add questions.

## Database Schema

The question field is stored in the QuizRounds DynamoDB table:

```
QuizRounds Table:
- roundId (String, Primary Key)
- sessionId (String, Sort Key)
- question (String) ← NEW FIELD
- audioKey (String)
- answers (List)
- correctAnswer (Number)
- roundNumber (Number)
- createdAt (String)
```

## Notes

- Question is a required field for new rounds
- Existing rounds without questions will display as empty until edited
- Question length is not limited, but keep it concise for better UX
- Question is displayed in both admin and participant views
