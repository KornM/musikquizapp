# Music Quiz Backend

A serverless backend for a music quiz application built with AWS CDK, Lambda, DynamoDB, S3, and API Gateway.

## Architecture

- **API Gateway**: REST API with CORS support
- **Lambda Functions**: Python 3.11 functions for all endpoints
- **DynamoDB**: Tables for admins, quiz sessions, rounds, and participants
- **S3**: Audio file storage
- **CloudFront**: CDN for frontend distribution

## Prerequisites

- Python 3.11+
- Node.js 18+ (for AWS CDK)
- AWS CLI configured with credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## Project Structure

```
.
├── cdk/                          # CDK infrastructure code
│   ├── app.py                    # CDK app entry point
│   ├── cdk.json                  # CDK configuration
│   ├── requirements.txt          # CDK dependencies
│   └── music_quiz_stack/         # Stack constructs
│       ├── stack.py              # Main stack
│       ├── lambda_functions.py   # Lambda definitions
│       ├── api_gateway.py        # API Gateway config
│       ├── database.py           # DynamoDB tables
│       └── storage.py            # S3 bucket
├── lambda/                       # Lambda function code
│   ├── common/                   # Shared utilities
│   │   ├── auth.py               # JWT & password utilities
│   │   ├── cors.py               # CORS headers
│   │   ├── db.py                 # DynamoDB helpers
│   │   └── errors.py             # Error responses
│   ├── admin_login/              # Admin authentication
│   ├── create_quiz/              # Create quiz session
│   ├── add_round/                # Add quiz round
│   ├── upload_audio/             # Upload audio file
│   ├── get_quiz/                 # Get quiz session
│   ├── list_sessions/            # List all sessions
│   ├── register_participant/     # Participant registration
│   ├── get_audio/                # Get audio presigned URL
│   └── generate_qr/              # Generate QR code data
├── scripts/                      # Utility scripts
│   └── create_admin.py           # Create initial admin user
└── tests/                        # Test suite
    └── unit/                     # Unit tests

```

## Deployment

### 1. Install Dependencies

```bash
# Install CDK dependencies
cd cdk
pip install -r requirements.txt
cd ..

# Install Lambda dependencies (if any additional packages needed)
pip install boto3 pyjwt bcrypt
```

### 2. Configure CDK

Edit `cdk/cdk.json` to set your configuration:

```json
{
  "context": {
    "domain_name": "musikquiz.yourdomain.com",
    "certificate_arn": "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID",
    "aws_account": "YOUR_AWS_ACCOUNT_ID",
    "aws_region": "us-east-1"
  }
}
```

### 3. Deploy the Stack

```bash
cd cdk

# Synthesize CloudFormation template (optional, for validation)
cdk synth

# Deploy to AWS
cdk deploy

# Note the API Gateway endpoint URL from the output
```

### 4. Create Initial Admin User

After deployment, create an admin user:

```bash
python scripts/create_admin.py --username admin --password YourSecurePassword123
```

## API Endpoints

### Admin Endpoints (Require JWT Token)

- `POST /admin/login` - Admin authentication
- `POST /admin/quiz-sessions` - Create quiz session
- `POST /admin/quiz-sessions/{sessionId}/rounds` - Add quiz round
- `POST /admin/audio` - Upload audio file

### Public Endpoints

- `GET /quiz-sessions` - List all quiz sessions
- `GET /quiz-sessions/{sessionId}` - Get quiz session with rounds
- `GET /quiz-sessions/{sessionId}/qr` - Get QR code registration URL
- `POST /participants/register` - Register participant
- `GET /audio/{audioKey}` - Get audio file (presigned URL)

## Authentication

### Admin Authentication

1. Login with username/password to get JWT token:
```bash
curl -X POST https://api.example.com/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

2. Use token in Authorization header:
```bash
curl -X POST https://api.example.com/admin/quiz-sessions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Quiz","description":"Fun quiz"}'
```

### Participant Authentication

Participants receive a token upon registration that can be used for future features.

## Testing

### Run Unit Tests

```bash
pytest tests/unit/
```

### Manual Testing

See tasks 13-18 in `.kiro/specs/music-quiz-backend/tasks.md` for detailed testing procedures.

## Environment Variables

Lambda functions use these environment variables (automatically set by CDK):

- `ADMINS_TABLE` - DynamoDB Admins table name
- `QUIZ_SESSIONS_TABLE` - DynamoDB Sessions table name
- `QUIZ_ROUNDS_TABLE` - DynamoDB Rounds table name
- `PARTICIPANTS_TABLE` - DynamoDB Participants table name
- `AUDIO_BUCKET` - S3 bucket for audio files
- `JWT_SECRET` - JWT signing secret (should use AWS Secrets Manager in production)
- `FRONTEND_URL` - Frontend URL for QR code generation

## Security Notes

- JWT_SECRET should be stored in AWS Secrets Manager for production
- Admin passwords are hashed with bcrypt
- S3 bucket is private; audio accessed via presigned URLs
- CORS is configured for cross-origin requests
- API Gateway has rate limiting enabled

## Troubleshooting

### CDK Deployment Fails

- Ensure AWS credentials are configured: `aws configure`
- Check CDK version: `cdk --version` (should be 2.x)
- Verify account/region in cdk.json matches your AWS account

### Lambda Function Errors

- Check CloudWatch Logs for detailed error messages
- Verify DynamoDB tables exist and have correct names
- Ensure Lambda has proper IAM permissions

### CORS Issues

- Verify CORS headers in Lambda responses
- Check API Gateway CORS configuration
- Test with browser dev tools network tab

## License

MIT
