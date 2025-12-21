# ⚡ Quick Start Guide

Fast reference for common operations.

## 🚀 First Time Setup

```bash
# 1. Deploy backend
cd cdk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cdk bootstrap
cdk deploy

# 2. Setup frontend
cd ../frontend
cp .env.example .env
# Edit .env with API Gateway URL from CDK output
npm install
npm run build

# 3. Create super admin
cd ../scripts
python create_super_admin.py
```

## 🔄 Daily Operations

### Deploy Changes

**Backend only:**
```bash
cd cdk
source venv/bin/activate
cdk deploy
```

**Frontend only:**
```bash
cd frontend
npm run build
# Upload to S3 or your hosting provider
```

**Both:**
```bash
cd cdk && cdk deploy && cd ../frontend && npm run build
```

### View Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/AddRoundFunction --follow

# All Lambda errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/SubmitAnswerFunction \
  --filter-pattern "ERROR"
```

### Database Operations

```bash
# List all tables
aws dynamodb list-tables

# Scan a table
aws dynamodb scan --table-name GlobalParticipants --max-items 10

# Get item
aws dynamodb get-item \
  --table-name Tenants \
  --key '{"tenantId": {"S": "your-tenant-id"}}'
```

## 🎯 Common Tasks

### Create a Tenant

1. Login as super admin: `/admin/login`
2. Go to "Tenant Management"
3. Click "Create Tenant"
4. Fill in details and save

### Create a Quiz

1. Login as tenant admin
2. Click "Create New Session"
3. Add title, description, media type
4. Add rounds with questions
5. Upload media if needed
6. Click "Start Round 1" when ready

### Test Participant Flow

1. Generate QR code from session
2. Scan with phone or visit URL
3. Register with name and avatar
4. Browse lobby and join session
5. Answer questions
6. View scoreboard

## 🐛 Troubleshooting

### "401 Unauthorized"
- Check if logged in
- Verify token in localStorage
- Try logging out and back in

### "Cannot submit answers"
- Check if session is active (not completed)
- Verify participant has joined session
- Check CloudWatch logs for errors

### "Session not found"
- Verify session exists in DynamoDB
- Check tenant ID matches
- Ensure session not deleted

### Frontend not loading
- Check API Gateway URL in `.env`
- Verify CORS configuration
- Check browser console for errors
- Clear browser cache

## 📊 Monitoring

### Key Metrics to Watch

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=SubmitAnswerFunction \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum

# API Gateway requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=MusicQuizApi \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## 🔐 Security

### Update JWT Secret

Edit `cdk/music_quiz_stack/lambda_functions.py`:
```python
"JWT_SECRET": "your-new-secure-secret-here"
```

Then deploy:
```bash
cd cdk && cdk deploy
```

### Reset Admin Password

```bash
cd scripts
python create_super_admin.py
# Choose same username to update password
```

## 💾 Backup

### Manual Backup

```bash
# Backup DynamoDB table
aws dynamodb create-backup \
  --table-name GlobalParticipants \
  --backup-name GlobalParticipants-backup-$(date +%Y%m%d)

# Backup S3 bucket
aws s3 sync s3://your-audio-bucket s3://your-backup-bucket
```

## 🧹 Cleanup

### Delete Old Sessions

```bash
# List sessions
aws dynamodb scan --table-name QuizSessions

# Delete session (use admin UI or API)
curl -X DELETE https://your-api/admin/quiz-sessions/{sessionId} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Clear Test Data

```bash
# Delete all participants from a session
curl -X DELETE https://your-api/admin/quiz-sessions/{sessionId}/participants \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📞 Quick Links

- **Admin Login**: `https://your-domain/admin/login`
- **Participant Lobby**: `https://your-domain/lobby`
- **API Docs**: `docs/API.md`
- **CloudWatch**: AWS Console → CloudWatch → Logs
- **DynamoDB**: AWS Console → DynamoDB → Tables

## 🎓 Tips

- Use Chrome DevTools Network tab to debug API calls
- Check CloudWatch logs immediately after errors
- Test with multiple participants using incognito windows
- Keep CDK and npm packages updated
- Monitor AWS costs in Billing Dashboard

---

**Need Help?** Check `DEPLOYMENT.md` for detailed instructions or `.kiro/session-notes.md` for recent changes.
