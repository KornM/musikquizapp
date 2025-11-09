# Implementation Plan

- [x] 1. Set up project structure and shared utilities
  - Create directory structure for CDK stack, Lambda functions, and shared utilities
  - Create Lambda common utilities directory with __init__.py
  - _Requirements: 4.3, 5.1_

- [x] 1.1 Implement CORS utility module
  - Write lambda/common/cors.py with add_cors_headers function
  - Ensure function adds Access-Control-Allow-Origin, Allow-Methods, and Allow-Headers
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 1.2 Implement error handling utility module
  - Write lambda/common/errors.py with error_response function
  - Ensure error responses include CORS headers and consistent JSON format
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 1.3 Implement authentication utility module
  - Write lambda/common/auth.py with JWT generation and validation functions
  - Implement hash_password and verify_password using bcrypt
  - _Requirements: 1.1, 1.3_

- [x] 1.4 Implement database utility module
  - Write lambda/common/db.py with DynamoDB helper functions
  - Create functions for common DynamoDB operations (get_item, put_item, query)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2. Set up CDK infrastructure foundation
  - Create cdk/app.py as CDK entry point
  - Create cdk/requirements.txt with AWS CDK dependencies
  - Create cdk/music_quiz_stack/__init__.py
  - _Requirements: 6.1, 6.2_

- [x] 2.1 Implement DynamoDB table definitions in CDK
  - Write cdk/music_quiz_stack/database.py
  - Define Admins, QuizSessions, QuizRounds, and Participants tables with proper keys and GSIs
  - _Requirements: 6.3, 8.1, 8.2, 8.3, 8.4_

- [x] 2.2 Implement S3 bucket configuration in CDK
  - Write cdk/music_quiz_stack/storage.py
  - Configure S3 bucket for audio storage with CORS and lifecycle policies
  - _Requirements: 6.3, 9.1, 9.2, 9.4_

- [x] 2.3 Implement Lambda function constructs in CDK
  - Write cdk/music_quiz_stack/lambda_functions.py
  - Define Lambda function constructs with proper IAM roles for DynamoDB and S3 access
  - _Requirements: 4.1, 4.5, 6.2, 6.4_

- [x] 2.4 Implement API Gateway configuration in CDK
  - Write cdk/music_quiz_stack/api_gateway.py
  - Configure REST API with all endpoints, methods, and CORS settings
  - Configure OPTIONS methods for preflight requests
  - _Requirements: 4.2, 4.4, 5.1, 5.5, 6.3_

- [x] 2.5 Implement main CDK stack
  - Write cdk/music_quiz_stack/stack.py
  - Integrate database, storage, Lambda, and API Gateway components
  - Configure CloudFront integration with ACM certificate
  - _Requirements: 6.1, 6.5, 7.2, 7.3_

- [x] 2.6 Create CDK configuration file
  - Write cdk/cdk.json with app entry point and context values
  - Include domain name, certificate ARN, AWS account, and region
  - _Requirements: 7.2, 7.3_

- [x] 3. Implement admin authentication Lambda
  - Create lambda/admin_login/handler.py
  - Implement POST /admin/login endpoint logic
  - Validate credentials against DynamoDB Admins table
  - Generate and return JWT token with CORS headers
  - _Requirements: 1.1, 1.3, 5.1, 10.1, 10.2_

- [x] 3.1 Write unit tests for admin login Lambda
  - Create tests/unit/test_admin_login.py
  - Test successful login, invalid credentials, and error cases
  - Mock DynamoDB calls
  - _Requirements: 1.1, 1.3_

- [x] 4. Implement create quiz session Lambda
  - Create lambda/create_quiz/handler.py
  - Implement POST /admin/quiz-sessions endpoint logic
  - Validate admin JWT token
  - Create new session in DynamoDB QuizSessions table
  - Return session details with CORS headers
  - _Requirements: 1.3, 2.1, 5.1, 10.1_

- [ ]* 4.1 Write unit tests for create quiz session Lambda
  - Create tests/unit/test_create_quiz.py
  - Test session creation with valid token and invalid token scenarios
  - Mock DynamoDB and JWT validation
  - _Requirements: 2.1, 1.3_

- [x] 5. Implement add quiz round Lambda
  - Create lambda/add_round/handler.py
  - Implement POST /admin/quiz-sessions/{sessionId}/rounds endpoint logic
  - Validate admin JWT token and session existence
  - Check round count limit (max 30 rounds)
  - Add round to DynamoDB QuizRounds table
  - Return round details with CORS headers
  - _Requirements: 1.3, 2.2, 2.3, 2.4, 5.1, 10.1_

- [ ]* 5.1 Write unit tests for add quiz round Lambda
  - Create tests/unit/test_add_round.py
  - Test adding rounds, max rounds validation, and invalid session scenarios
  - Mock DynamoDB operations
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 6. Implement upload audio Lambda
  - Create lambda/upload_audio/handler.py
  - Implement POST /admin/audio endpoint logic
  - Validate admin JWT token
  - Generate unique S3 key for audio file
  - Upload audio data to S3 bucket
  - Return audio key and presigned URL with CORS headers
  - _Requirements: 1.3, 9.1, 9.2, 9.3, 5.1, 10.1_

- [ ]* 6.1 Write unit tests for upload audio Lambda
  - Create tests/unit/test_upload_audio.py
  - Test audio upload with valid token and various audio formats
  - Mock S3 operations
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 7. Implement get quiz session Lambda
  - Create lambda/get_quiz/handler.py
  - Implement GET /quiz-sessions/{sessionId} endpoint logic
  - Retrieve session from DynamoDB QuizSessions table
  - Query associated rounds from QuizRounds table
  - Return session with rounds array and CORS headers
  - _Requirements: 2.5, 5.1, 10.1_

- [ ]* 7.1 Write unit tests for get quiz session Lambda
  - Create tests/unit/test_get_quiz.py
  - Test retrieving existing and non-existing sessions
  - Mock DynamoDB query operations
  - _Requirements: 2.5_

- [x] 8. Implement list quiz sessions Lambda
  - Create lambda/list_sessions/handler.py
  - Implement GET /quiz-sessions endpoint logic
  - Scan or query all sessions from DynamoDB QuizSessions table
  - Return sessions array with CORS headers
  - _Requirements: 2.6, 5.1, 10.1_

- [ ]* 8.1 Write unit tests for list sessions Lambda
  - Create tests/unit/test_list_sessions.py
  - Test listing sessions with various data scenarios
  - Mock DynamoDB scan operations
  - _Requirements: 2.6_

- [x] 9. Implement register participant Lambda
  - Create lambda/register_participant/handler.py
  - Implement POST /participants/register endpoint logic
  - Validate session existence
  - Create participant record in DynamoDB Participants table
  - Generate participant token
  - Return participant ID and token with CORS headers
  - _Requirements: 1.2, 1.4, 3.3, 3.4, 5.1, 10.1_

- [ ]* 9.1 Write unit tests for register participant Lambda
  - Create tests/unit/test_register_participant.py
  - Test participant registration with valid and invalid session IDs
  - Mock DynamoDB operations
  - _Requirements: 1.2, 1.4, 3.3, 3.4_

- [x] 10. Implement get audio Lambda
  - Create lambda/get_audio/handler.py
  - Implement GET /audio/{audioKey} endpoint logic
  - Generate presigned S3 URL for audio file
  - Return presigned URL or redirect with CORS headers
  - _Requirements: 9.4, 5.1, 10.1_

- [ ]* 10.1 Write unit tests for get audio Lambda
  - Create tests/unit/test_get_audio.py
  - Test presigned URL generation for valid and invalid audio keys
  - Mock S3 operations
  - _Requirements: 9.4_

- [x] 11. Implement generate QR code data Lambda
  - Create lambda/generate_qr/handler.py
  - Implement GET /quiz-sessions/{sessionId}/qr endpoint logic
  - Construct registration URL for the session
  - Return registration URL with CORS headers
  - _Requirements: 3.1, 3.2, 5.1, 10.1_

- [ ]* 11.1 Write unit tests for generate QR Lambda
  - Create tests/unit/test_generate_qr.py
  - Test QR data generation for valid sessions
  - _Requirements: 3.1_

- [x] 12. Create initial admin user setup script
  - Write a Python script to create initial admin user in DynamoDB
  - Script should hash password and insert into Admins table
  - Can be run after CDK deployment to bootstrap admin access
  - _Requirements: 1.1, 8.3_

- [x] 13. Deploy and test CDK stack
  - Run cdk synth to validate CloudFormation template
  - Run cdk deploy to deploy stack to AWS
  - Verify all resources created successfully (Lambda, API Gateway, DynamoDB, S3)
  - Note API Gateway endpoint URL
  - _Requirements: 6.5_

- [x] 14. Test CORS configuration with browser
  - Use browser dev tools to test OPTIONS preflight requests
  - Test actual API calls from a simple HTML page
  - Verify CORS headers present in both success and error responses
  - Test with different HTTP methods (GET, POST)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.4_

- [x] 15. Test admin authentication flow end-to-end
  - Run initial admin setup script to create admin user
  - Test POST /admin/login with valid credentials
  - Verify JWT token returned
  - Test protected endpoints with valid token
  - Test protected endpoints with invalid token (should return 401)
  - _Requirements: 1.1, 1.3_

- [x] 16. Test quiz session creation and management flow
  - Test POST /admin/quiz-sessions to create session
  - Test POST /admin/audio to upload audio file
  - Test POST /admin/quiz-sessions/{id}/rounds to add rounds
  - Test adding 30 rounds successfully
  - Test that 31st round returns 409 error
  - Test GET /quiz-sessions/{id} to retrieve session with rounds
  - Test GET /quiz-sessions to list all sessions
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 9.1, 9.2_

- [x] 17. Test participant registration flow
  - Test GET /quiz-sessions/{id}/qr to get registration URL
  - Test POST /participants/register with valid session ID
  - Verify participant token returned
  - Test registration with invalid session ID (should return 404)
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 18. Test audio file retrieval
  - Test GET /audio/{key} with valid audio key
  - Verify presigned URL returned or redirect works
  - Test accessing presigned URL in browser
  - Verify audio file plays correctly
  - Test with invalid audio key (should return 404)
  - _Requirements: 9.4_

- [ ]* 19. Create integration test suite
  - Create tests/integration/test_api_endpoints.py
  - Write integration tests that call actual deployed API endpoints
  - Test complete workflows from admin login through quiz creation
  - _Requirements: All_

- [ ]* 20. Create CORS-specific integration tests
  - Create tests/integration/test_cors.py
  - Write tests that verify CORS headers from actual API
  - Test preflight OPTIONS requests
  - Test CORS headers in error responses
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 21. Document API endpoints
  - Create API documentation with request/response examples
  - Document authentication requirements
  - Document error codes and messages
  - Include CORS configuration details
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 22. Create deployment documentation
  - Document CDK deployment steps
  - Document initial admin setup process
  - Document environment configuration
  - Include troubleshooting guide for common issues
  - _Requirements: 6.5_
