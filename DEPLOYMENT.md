# Music Quiz - Deployment & Usage Guide

## 🎉 Project Status: FULLY FUNCTIONAL

Your Music Quiz application is now deployed and working!

## What's Working

### Backend (AWS - eu-central-1)
✅ All Lambda functions deployed
✅ DynamoDB tables configured
✅ S3 audio storage
✅ API Gateway with CORS
✅ Admin authentication
✅ Session & round management
✅ Audio upload
✅ QR code generation

### Frontend (Vue.js + Vuetify)
✅ Admin login
✅ Dashboard with session management
✅ Create quiz sessions
✅ Add rounds with audio upload (drag & drop)
✅ View session details with rounds
✅ QR code generation
✅ Presentation mode for beamer

## Quick Start

### 1. Create Admin User

```bash
python scripts/create_admin.py --username admin --password YourPassword123
```

### 2. Start Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env and add your API Gateway URL
npm run dev
```

### 3. Login & Create Quiz

1. Open http://localhost:3000
2. Login with your admin credentials
3. Click "Create New Session"
4. Add rounds with audio files
5. Generate QR code for participants
6. Open presentation mode

## API Endpoint

Your API is deployed at:
```
https://YOUR_API_ID.execute-api.eu-central-1.amazonaws.com/prod
```

Find your API ID in AWS Console → API Gateway

## Features

### Admin Workflow
1. **Login** - Secure JWT authentication
2. **Create Sessions** - Title and description
3. **Add Rounds** - Upload audio + 4 answers
4. **Generate QR** - For participant registration
5. **Present** - Fullscreen mode with audio playback

### Presentation Mode
- Fullscreen display for beamer
- Audio player with controls
- Show/hide correct answer
- Navigate between rounds
- Large, readable answer options

### Technical Details
- **Max Rounds**: 30 per session
- **Audio Formats**: MP3, WAV, OGG
- **Max File Size**: 10MB
- **Token Expiry**: 24 hours

## Troubleshooting

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Can't login
- Check admin user exists in DynamoDB Admins table
- Verify API URL in frontend/.env

### Audio upload fails
- Check file size < 10MB
- Verify S3 bucket permissions
- Check file format (MP3/WAV/OGG)

## Architecture

```
Frontend (Vue.js)
    ↓
API Gateway
    ↓
Lambda Functions
    ↓
DynamoDB + S3
```

## Next Steps (Optional)

- Implement participant registration view
- Add participant quiz interface
- Real-time updates with WebSockets
- Leaderboard functionality
- Analytics dashboard

## Support

Check CloudWatch Logs for Lambda errors:
```bash
aws logs tail /aws/lambda/FUNCTION_NAME --follow
```

## Congratulations! 🎊

Your Music Quiz application is ready to use!
