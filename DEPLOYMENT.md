# 🚀 Deployment Guide

Complete guide for deploying the Music Quiz Application to AWS.

## 📋 Prerequisites

### Required Tools
- **AWS CLI**: Configured with appropriate credentials
- **Node.js**: Version 18 or higher
- **Python**: Version 3.11 or higher
- **AWS CDK**: Install globally with `npm install -g aws-cdk`
- **Git**: For cloning the repository

### AWS Requirements
- AWS Account with admin access (or appropriate IAM permissions)
- AWS region selected (default: us-east-1)
- Sufficient service limits for:
  - Lambda functions (~35 functions)
  - DynamoDB tables (7 tables)
  - S3 buckets (1 bucket)
  - CloudFront distribution (1 distribution)
  - API Gateway (1 REST API)

## 🔧 Step-by-Step Deployment

### 1. Clone Repository

```bash
git clone <repository-url>
cd musikquizapp
```

### 2. Deploy Backend Infrastructure

```bash
cd cdk

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy

# Note the outputs - you'll need:
# - ApiGatewayUrl
# - CloudFrontDomain
# - All DynamoDB table names
```

**Expected Deployment Time**: 10-15 minutes

### 3. Configure Frontend

```bash
cd ../frontend

# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Update `.env` with your API Gateway URL from CDK output:
```env
VITE_API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/prod
```

### 4. Build and Deploy Frontend

```bash
# Install dependencies
npm install

# Build for production
npm run build

# The dist/ folder is ready for deployment
```

**Frontend Deployment Options:**

**Option A: Deploy to S3/CloudFront (Recommended)**
```bash
# Upload to S3 bucket (created by CDK)
aws s3 sync dist/ s3://your-frontend-bucket/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

**Option B: Deploy to Vercel/Netlify**
- Connect your repository
- Set build command: `npm run build`
- Set publish directory: `dist`
- Add environment variable: `VITE_API_BASE_URL`

### 5. Create Super Admin Account

```bash
cd ../scripts

# Run the super admin creation script
python3 create_super_admin.py

# Follow the prompts to create your super admin account
# Save the credentials securely!
```

### 6. Create First Tenant

1. Login to admin panel: `https://your-domain/admin/login`
2. Use super admin credentials
3. Navigate to "Tenant Management"
4. Click "Create Tenant"
5. Fill in tenant details
6. Create a tenant admin for the new tenant

### 7. Verify Deployment

**Backend Health Check:**
```bash
# Test API Gateway
curl https://your-api-gateway-url/quiz-sessions

# Should return: {"sessions": []}
```

**Frontend Check:**
- Visit your CloudFront domain
- Should redirect to `/admin/login`
- Login page should load without errors

**Database Check:**
```bash
# List DynamoDB tables
aws dynamodb list-tables

# Should see all tables:
# - Tenants
# - Admins
# - GlobalParticipants
# - SessionParticipations
# - QuizSessions
# - QuizRounds
# - Answers
```

## 🔄 Updates and Redeployment

### Backend Updates

```bash
cd cdk
source venv/bin/activate
cdk deploy
```

### Frontend Updates

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://your-frontend-bucket/ --delete
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

### Lambda Function Updates

If you only changed Lambda code:
```bash
cd cdk
cdk deploy --hotswap  # Faster deployment for Lambda-only changes
```

## 🐛 Troubleshooting

### Common Issues

**1. CDK Bootstrap Error**
```bash
# Solution: Bootstrap with explicit account/region
cdk bootstrap aws://ACCOUNT-ID/REGION
```

**2. Lambda Permission Errors**
- Check CloudWatch logs: `/aws/lambda/function-name`
- Verify IAM roles have DynamoDB permissions
- Run: `cdk deploy` to update permissions

**3. CORS Errors in Frontend**
- Verify API Gateway URL in `.env`
- Check CORS configuration in Lambda responses
- Clear browser cache

**4. 401 Authentication Errors**
- Verify JWT secret is consistent
- Check token expiration
- Ensure admin account exists in DynamoDB

**5. File Upload Failures**
- Check S3 bucket permissions
- Verify Lambda has S3 write access
- Check file size limits (default: 10MB)

### Viewing Logs

**Lambda Logs:**
```bash
# View recent logs
aws logs tail /aws/lambda/FUNCTION_NAME --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/FUNCTION_NAME \
  --filter-pattern "ERROR"
```

**API Gateway Logs:**
- Enable in AWS Console: API Gateway → Stages → Logs
- View in CloudWatch Logs

## 🔐 Security Hardening

### Production Checklist

- [ ] Update JWT secret in Lambda environment variables
- [ ] Enable CloudFront HTTPS only
- [ ] Configure custom domain with SSL certificate
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Set up CloudWatch alarms for errors
- [ ] Enable AWS WAF on API Gateway
- [ ] Configure S3 bucket policies
- [ ] Review IAM roles and permissions
- [ ] Enable CloudTrail for audit logging
- [ ] Set up backup strategy

### Environment Variables to Update

**Lambda Functions** (via CDK):
```python
"JWT_SECRET": "your-secure-secret-here",  # Change this!
"FRONTEND_URL": "https://your-domain.com",
```

## 📊 Monitoring

### CloudWatch Dashboards

Create dashboards for:
- Lambda invocations and errors
- API Gateway requests and latency
- DynamoDB read/write capacity
- S3 bucket metrics

### Alarms

Set up alarms for:
- Lambda error rate > 5%
- API Gateway 5xx errors
- DynamoDB throttling
- High Lambda duration

## 💰 Cost Optimization

### Estimated Monthly Costs (Low Traffic)
- Lambda: $5-10
- DynamoDB: $5-15 (on-demand pricing)
- S3: $1-5
- CloudFront: $1-10
- API Gateway: $3-10
- **Total**: ~$15-50/month

### Cost Reduction Tips
- Use DynamoDB on-demand pricing for variable traffic
- Enable S3 lifecycle policies for old media
- Use CloudFront caching effectively
- Set Lambda memory appropriately (256MB default)
- Clean up old quiz sessions periodically

## 🔄 Backup and Recovery

### Backup Strategy

**DynamoDB:**
- Point-in-time recovery enabled by default
- On-demand backups: AWS Console → DynamoDB → Backups

**S3:**
- Versioning enabled on audio bucket
- Cross-region replication (optional)

**Recovery:**
```bash
# Restore DynamoDB table
aws dynamodb restore-table-from-backup \
  --target-table-name NewTableName \
  --backup-arn arn:aws:dynamodb:region:account:table/table-name/backup/backup-name
```

## 📞 Support

For deployment issues:
1. Check CloudWatch logs
2. Review CDK deployment outputs
3. Verify all prerequisites are met
4. Check AWS service quotas

## 🎉 Post-Deployment

After successful deployment:
1. Create your first tenant
2. Create a tenant admin
3. Create a test quiz session
4. Test participant registration flow
5. Verify scoring and leaderboard
6. Share QR code with test participants

---

**Deployment Version**: 2.1.0  
**Last Updated**: December 21, 2024
