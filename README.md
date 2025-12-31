# 🎵 Music Quiz Application

A modern, multi-tenant music quiz application built with AWS serverless architecture. Create engaging music quizzes with audio clips, images, or text-only questions. Perfect for events, parties, or educational purposes.

## ✨ Features

### 🎯 Core Functionality
- **Multi-Tenant Architecture**: Isolated environments for different organizations
- **Flexible Quiz Types**: Audio, image, or text-based questions
- **Real-Time Scoring**: Instant feedback with time-based point system
- **Global Leaderboard**: Aggregate scores across all sessions
- **QR Code Registration**: Easy participant onboarding
- **Presentation Mode**: Full-screen quiz display for events

### 👥 User Roles
- **Super Admin**: Manage tenants and tenant admins
- **Tenant Admin**: Create and manage quiz sessions
- **Participants**: Join sessions and compete

### 🎮 Participant Experience
- **One-Time Registration**: Register once per tenant, join multiple sessions
- **Lobby System**: Browse and join available quiz sessions
- **Live Scoring**: See points earned in real-time
- **Profile Management**: Customize name and avatar
- **Mobile-Friendly**: Responsive design for all devices

### 🎨 Admin Features
- **Session Management**: Create, edit, and complete quiz sessions
- **Round Management**: Add multiple rounds with 4 answer options
- **Media Upload**: Support for audio files and images
- **Participant Management**: View and manage session participants
- **Live Scoreboard**: Monitor participant performance
- **Global Analytics**: View aggregate scores across all sessions

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Vue 3 + Vuetify 3
- **Backend**: AWS Lambda (Python 3.11)
- **Database**: DynamoDB
- **Storage**: S3 + CloudFront
- **API**: API Gateway REST API
- **Infrastructure**: AWS CDK (Python)

### Key Components
- **GlobalParticipants**: Tenant-wide participant profiles
- **SessionParticipations**: Tracks participant session enrollment
- **Quiz Sessions**: Quiz metadata and configuration
- **Quiz Rounds**: Individual questions with answers
- **Answers**: Participant responses with scoring

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- Node.js 18+ and npm
- Python 3.11+
- AWS CDK CLI (`npm install -g aws-cdk`)

### Deployment

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd musikquizapp
   ```

2. **Deploy Backend**
   ```bash
   cd cdk
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cdk bootstrap  # First time only
   cdk deploy
   ```
   
   Save the CDK outputs - you'll need the `ApiGatewayUrl`.

3. **Configure Frontend**
   ```bash
   cd ../frontend
   cp .env.example .env
   # Edit .env with your API Gateway URL from CDK output
   npm install
   npm run build
   ```

4. **Create Super Admin**
   ```bash
   cd ../scripts
   python3 create_super_admin.py
   ```

5. **Access Application**
   - Admin: `https://your-cloudfront-domain/admin/login`
   - Participant: `https://your-cloudfront-domain/lobby`

For detailed deployment instructions, see `DEPLOYMENT.md`.

## 📖 User Guide

### For Admins

**Creating a Quiz Session:**
1. Login to admin dashboard
2. Click "Create New Session"
3. Enter title, description, and select media type
4. Add rounds with questions and answers
5. Upload audio/images if needed
6. Start the session when ready

**Managing a Session:**
- **Start Session**: Change status from draft to active
- **Start Round**: Begin a specific round for participants
- **View Scoreboard**: See live participant rankings for current session
- **View Global Scoreboard**: See aggregate scores across all sessions
- **Complete Session**: End the session and prevent new answers
- **Generate QR Code**: Share for easy participant registration

### For Participants

**Joining a Quiz:**
1. Scan QR code or use registration link
2. Enter your name and choose an avatar
3. Browse available sessions in the lobby
4. Click "Join Quiz" on an active session
5. Answer questions as they appear
6. View your score and ranking

**Scoring System:**
- **10 points**: Answer within 2 seconds
- **8 points**: Answer within 5 seconds
- **5 points**: Correct answer (slower)
- **0 points**: Incorrect answer

## 🔧 Configuration

### Environment Variables

**Frontend** (`.env`):
```env
VITE_API_BASE_URL=https://your-api-gateway-url
```

**Backend** (CDK):
- Configured automatically via CDK deployment
- JWT secret should be updated in production
- Frontend URL configured in Lambda environment

### Customization

**Branding:**
- Update `frontend/index.html` for title and meta tags
- Modify color schemes in Vuetify configuration
- Replace icons and logos as needed

**Limits:**
- Max rounds per session: 30
- Answer options per question: 4
- File upload size: Configured in Lambda

## 🔐 Security

- **Authentication**: JWT-based with role-based access control
- **Multi-Tenancy**: Data isolation per tenant
- **API Security**: CORS configured, token validation
- **Data Protection**: DynamoDB encryption at rest
- **S3 Security**: Signed URLs for media access

## 📊 Database Schema

### Tables
- **Tenants**: Organization/tenant information
- **Admins**: Admin user accounts (super admins and tenant admins)
- **GlobalParticipants**: Participant profiles (tenant-wide, one registration per tenant)
- **SessionParticipations**: Tracks which participants joined which sessions
- **QuizSessions**: Quiz session metadata and configuration
- **QuizRounds**: Individual questions with 4 answer options
- **Answers**: Participant responses with timestamps and scoring

### Key Features
- **Multi-tenancy**: Complete data isolation between tenants
- **Global Participants**: Register once per tenant, join multiple sessions
- **Session Lifecycle**: Draft → Active → Completed states
- **Time-based Scoring**: Points awarded based on answer speed
- **Global Leaderboard**: Aggregate scores across all sessions per tenant

## 🧪 Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm run test
```

## 📝 API Documentation

See `docs/API.md` for detailed API documentation.

## 🤝 Contributing

This is a private project. For questions or issues, contact the development team.

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For deployment issues or questions:
1. Check CloudWatch logs for Lambda errors
2. Verify DynamoDB table permissions
3. Ensure API Gateway CORS is configured
4. Review CDK deployment outputs

## 🎉 Acknowledgments

Built with modern serverless technologies for scalability and performance.

---

**Version**: 2.1.0  
**Last Updated**: December 21, 2024
