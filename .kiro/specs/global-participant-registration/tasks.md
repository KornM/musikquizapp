# Implementation Plan

- [x] 1. Database Schema Updates
  - Create new DynamoDB tables and update existing ones with tenant support
  - _Requirements: 8.3, 11.5, 14.1, 16.1, 16.2_

- [x] 1.1 Create Tenants table
  - Define Tenants table with tenantId as primary key
  - Add GSI for status-based queries (StatusIndex)
  - Include fields: tenantId, name, description, status, createdAt, updatedAt, settings
  - _Requirements: 8.3_

- [x] 1.2 Create GlobalParticipants table
  - Define GlobalParticipants table with participantId as primary key
  - Add GSI for tenant-based queries (TenantIndex: tenantId, createdAt)
  - Include fields: participantId, tenantId, name, avatar, token, createdAt, updatedAt
  - _Requirements: 11.5, 16.1_

- [x] 1.3 Create SessionParticipations table
  - Define SessionParticipations table with participationId as primary key
  - Add GSI for session-based queries (SessionIndex: sessionId, joinedAt)
  - Add GSI for participant-based queries (ParticipantIndex: participantId, joinedAt)
  - Include fields: participationId, participantId, sessionId, tenantId, joinedAt, totalPoints, correctAnswers
  - _Requirements: 16.2_

- [x] 1.4 Update Admins table schema
  - Add tenantId field to Admins table (nullable for super admins)
  - Add role field (super_admin | tenant_admin)
  - Add GSI for tenant-based admin queries (TenantIndex: tenantId, createdAt)
  - Update CDK database stack definition
  - _Requirements: 9.3, 14.1_

- [x] 1.5 Update QuizSessions table schema
  - Add tenantId field to QuizSessions table
  - Add GSI for tenant-based session queries (TenantStatusIndex: tenantId, createdAt)
  - Update CDK database stack definition
  - _Requirements: 10.5, 14.1_

- [x] 1.6 Update Answers table schema
  - Add tenantId field to Answers table for denormalized filtering
  - Add participationId field to link to SessionParticipations
  - Update CDK database stack definition
  - _Requirements: 14.1_

- [x] 2. Tenant Management Backend
  - Implement Lambda functions for tenant CRUD operations
  - _Requirements: 8.1, 8.2, 8.4, 8.5_

- [x] 2.1 Create tenant creation Lambda
  - Implement POST /super-admin/tenants endpoint
  - Generate unique tenant ID (UUID)
  - Validate required fields (name required, description optional)
  - Store tenant in Tenants table with status=active
  - Return tenant details including tenantId
  - _Requirements: 8.1, 8.2_

- [x] 2.2 Write property test for tenant creation
  - **Property 24: Unique tenant ID generation**
  - **Property 25: Tenant creation validation**
  - **Validates: Requirements 8.1, 8.2**

- [x] 2.3 Create tenant listing Lambda
  - Implement GET /super-admin/tenants endpoint
  - Query all tenants from Tenants table
  - Return list with name, createdAt, status for each tenant
  - Support filtering by status (optional)
  - _Requirements: 8.4_

- [x] 2.4 Write property test for tenant listing
  - **Property 26: Tenant list completeness**
  - **Validates: Requirements 8.4**

- [x] 2.5 Create tenant update Lambda
  - Implement PUT /super-admin/tenants/{tenantId} endpoint
  - Validate tenant exists
  - Update name, description, or status
  - Return updated tenant details
  - _Requirements: 8.5_

- [x] 2.6 Create tenant deletion Lambda
  - Implement DELETE /super-admin/tenants/{tenantId} endpoint
  - Mark tenant as inactive (soft delete)
  - Prevent new session creation for inactive tenants
  - Return success confirmation
  - _Requirements: 8.5_

- [x] 2.7 Write property test for tenant deletion
  - **Property 27: Tenant deletion blocks new sessions**
  - **Property 43: Tenant deletion cascades**
  - **Validates: Requirements 8.5, 14.3**

- [-] 3. Tenant Admin Management Backend
  - Implement Lambda functions for managing tenant administrators
  - _Requirements: 9.1, 9.2, 9.4, 13.2, 13.3, 13.4, 13.5_

- [x] 3.1 Create tenant admin creation Lambda
  - Implement POST /super-admin/tenants/{tenantId}/admins endpoint
  - Validate required fields (username, password, tenantId)
  - Check tenant exists and is active
  - Hash password using bcrypt
  - Generate unique admin ID
  - Store admin with role=tenant_admin and tenantId
  - Return admin details (without password)
  - _Requirements: 9.1, 9.2_

- [x] 3.2 Write property test for tenant admin creation
  - **Property 28: Tenant admin association**
  - **Property 29: Tenant admin creation validation**
  - **Validates: Requirements 9.1, 9.2**

- [x] 3.3 Create tenant admin listing Lambda
  - Implement GET /super-admin/tenants/{tenantId}/admins endpoint
  - Query admins by tenantId using TenantIndex GSI
  - Return list of admins for the specified tenant
  - _Requirements: 9.5_

- [x] 3.4 Create tenant admin update Lambda
  - Implement PUT /super-admin/admins/{adminId} endpoint
  - Support updating username, email, tenantId
  - Validate new tenantId exists if changing tenant
  - Return updated admin details
  - _Requirements: 13.2, 13.5_

- [x] 3.5 Write property test for admin updates
  - **Property 38: Admin update persistence**
  - **Property 41: Admin tenant reassignment**
  - **Validates: Requirements 13.2, 13.5**

- [x] 3.6 Create tenant admin deletion Lambda
  - Implement DELETE /super-admin/admins/{adminId} endpoint
  - Mark admin as deleted or remove from database
  - Invalidate admin's tokens
  - Return success confirmation
  - _Requirements: 13.3_

- [x] 3.7 Write property test for admin deletion
  - **Property 39: Admin deletion blocks access**
  - **Validates: Requirements 13.3**

- [x] 3.8 Create admin password reset Lambda
  - Implement POST /super-admin/admins/{adminId}/reset-password endpoint
  - Validate new password meets requirements
  - Hash new password using bcrypt
  - Update admin record
  - Return success confirmation
  - _Requirements: 13.4_

- [x] 3.9 Write property test for password changes
  - **Property 40: Password change effectiveness**
  - **Validates: Requirements 13.4**

- [-] 4. Enhanced Admin Authentication
  - Update admin login to include tenant context in JWT tokens
  - _Requirements: 9.4, 10.1, 10.2, 10.3_

- [x] 4.1 Update admin login Lambda
  - Modify POST /admin/login endpoint
  - Query admin by username using UsernameIndex
  - Verify password hash
  - Include tenantId and role in JWT token payload
  - Return token with tenantId in response body
  - _Requirements: 9.4_

- [x] 4.2 Write property test for admin login
  - **Property 30: Admin login returns tenant context**
  - **Validates: Requirements 9.4**

- [x] 4.3 Create tenant validation middleware
  - Implement middleware to extract tenantId from JWT
  - Validate tenant exists and is active
  - Attach tenant context to request
  - Use in all tenant-aware endpoints
  - _Requirements: 10.3_

- [x] 4.4 Update session creation Lambda
  - Modify POST /admin/sessions endpoint
  - Extract tenantId from authenticated admin's JWT
  - Automatically add tenantId to session record
  - Validate tenant is active before creating session
  - _Requirements: 10.1_

- [x] 4.5 Write property test for session tenant inheritance
  - **Property 31: Session inherits admin tenant**
  - **Validates: Requirements 10.1**

- [x] 4.6 Update session listing Lambda
  - Modify GET /admin/sessions endpoint
  - Filter sessions by authenticated admin's tenantId
  - Only return sessions belonging to admin's tenant
  - _Requirements: 10.2_

- [x] 4.7 Write property test for session filtering
  - **Property 32: Session list tenant filtering**
  - **Validates: Requirements 10.2, 10.4**

- [x] 4.8 Update session detail Lambda
  - Modify GET /admin/sessions/{sessionId} endpoint
  - Validate session's tenantId matches admin's tenantId
  - Return 403 Forbidden if tenant mismatch
  - _Requirements: 10.3_

- [x] 4.9 Write property test for cross-tenant access
  - **Property 33: Cross-tenant session access denial**
  - **Validates: Requirements 10.3, 14.4**

- [-] 5. Global Participant Registration
  - Implement global participant system with tenant association
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.3, 11.1_

- [x] 5.1 Create global participant registration Lambda
  - Implement POST /participants/register endpoint
  - Accept tenantId, name, avatar in request
  - Generate unique participantId (UUID)
  - Validate tenant exists and is active
  - Generate JWT token with participantId and tenantId
  - Store in GlobalParticipants table
  - Return participantId, token, and profile data
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1_

- [x] 5.2 Write property tests for participant registration
  - **Property 1: Global participant creation generates unique ID**
  - **Property 2: Participant profile storage**
  - **Property 3: Profile independence from sessions**
  - **Property 4: Authentication token generation**
  - **Property 5: Participant ID in response**
  - **Property 34: Participant tenant association**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 11.1**

- [x] 5.3 Create participant profile retrieval Lambda
  - Implement GET /participants/{participantId} endpoint
  - Query GlobalParticipants table by participantId
  - Validate participant exists
  - Return name, avatar, tenantId, createdAt
  - _Requirements: 2.1_

- [x] 5.4 Write property test for profile retrieval
  - **Property 6: Profile retrieval**
  - **Validates: Requirements 2.1**

- [x] 5.5 Create participant profile update Lambda
  - Implement PUT /participants/{participantId} endpoint
  - Validate authentication token
  - Accept updated name and/or avatar
  - Update GlobalParticipants record
  - Return updated profile
  - _Requirements: 2.3_

- [x] 5.6 Write property tests for profile updates
  - **Property 7: Profile update persistence**
  - **Property 8: Profile updates propagate to sessions**
  - **Validates: Requirements 2.3, 2.4**

- [x] 5.7 Create participant authentication middleware
  - Implement middleware to validate participant JWT tokens
  - Extract participantId and tenantId from token
  - Validate token signature and expiration
  - Attach participant context to request
  - _Requirements: 7.3, 7.4, 7.5_

- [x] 5.8 Write property tests for authentication
  - **Property 22: Unauthorized access denial**
  - **Property 23: Token contains participant ID**
  - **Validates: Requirements 7.3, 7.4, 7.5**

- [x] 6. Session Participation Auto-Registration
  - Implement automatic session participation when participants join sessions
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 11.2, 11.4_

- [x] 6.1 Create session join Lambda
  - Implement POST /sessions/{sessionId}/join endpoint
  - Validate participant authentication token
  - Verify session exists and belongs to participant's tenant
  - Check if participation already exists (idempotent)
  - Generate unique participationId
  - Create SessionParticipation record with totalPoints=0
  - Record joinedAt timestamp
  - Return participation details
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 11.2_

- [x] 6.2 Write property tests for session joining
  - **Property 9: Auto-creation of session participation**
  - **Property 10: Participation record linkage**
  - **Property 11: Initial score is zero**
  - **Property 12: Join timestamp recording**
  - **Property 35: Cross-tenant session join denial**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 11.2, 11.3**

- [x] 6.3 Update get participants Lambda
  - Modify GET /admin/sessions/{sessionId}/participants endpoint
  - Join SessionParticipations with GlobalParticipants
  - Return combined data: name, avatar from GlobalParticipants + totalPoints from SessionParticipations
  - Filter by session's tenantId
  - _Requirements: 4.1, 4.2, 4.3, 11.4_

- [x] 6.4 Write property tests for participant listing
  - **Property 13: Complete participant list for session**
  - **Property 14: Participant list contains required fields**
  - **Property 15: Participant list reflects current profile**
  - **Property 36: Participant list tenant filtering**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 11.4**

- [x] 7. Answer Submission and Scoring
  - Update answer submission to use SessionParticipations
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7.1 Update submit answer Lambda
  - Modify POST /participants/answers endpoint
  - Look up SessionParticipation by participantId and sessionId
  - Store participationId in Answer record
  - Add tenantId to Answer record (denormalized)
  - Calculate points based on correctness and timing
  - Update SessionParticipation.totalPoints
  - Update SessionParticipation.correctAnswers if correct
  - _Requirements: 5.1, 5.2_

- [x] 7.2 Write property tests for answer submission
  - **Property 16: Answer linked to participation**
  - **Property 17: Score isolation per session**
  - **Property 18: Independent participation records**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 7.3 Update get scoreboard Lambda
  - Modify GET /sessions/{sessionId}/scoreboard endpoint
  - Query SessionParticipations by sessionId
  - Join with GlobalParticipants for name and avatar
  - Filter by session's tenantId
  - Sort by totalPoints descending
  - Return session-specific scores only
  - _Requirements: 5.4_

- [x] 7.4 Write property tests for scoreboard
  - **Property 19: Scoreboard session specificity**
  - **Property 20: Score and answer persistence**
  - **Validates: Requirements 5.4, 5.5**

- [x] 8. Tenant Isolation Enforcement
  - Add tenant validation to all tenant-aware endpoints
  - _Requirements: 14.2, 14.4_

- [x] 8.1 Update all query operations
  - Add tenantId filter to all DynamoDB queries for tenant-specific tables
  - Update scan operations to include tenantId in filter expression
  - Ensure GSI queries use tenantId as partition key where applicable
  - _Requirements: 14.2_

- [x] 8.2 Write property test for query isolation
  - **Property 42: Query tenant isolation**
  - **Validates: Requirements 14.2**

- [x] 8.3 Add cross-tenant access validation
  - Implement validation function to check tenant access
  - Use in all endpoints that access tenant-specific resources
  - Return 403 Forbidden for cross-tenant access attempts
  - Log all cross-tenant access attempts for security monitoring
  - _Requirements: 14.4_

- [x] 9. Frontend - Super Admin UI
  - Create super admin interface for tenant and admin management
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 13.1_

- [x] 9.1 Create tenant management page
  - Create /super-admin/tenants route
  - Display list of all tenants in a table
  - Show tenant name, status, created date
  - Add "Create Tenant" button
  - Add edit/delete actions for each tenant
  - _Requirements: 12.1_

- [x] 9.2 Create tenant creation form
  - Create modal/page for tenant creation
  - Add form fields: name (required), description (optional)
  - Validate name is not empty
  - Call POST /super-admin/tenants API
  - Show success/error messages
  - Refresh tenant list on success
  - _Requirements: 12.2, 12.3_

- [x] 9.3 Write property test for tenant form submission
  - **Property 37: Tenant form submission creates tenant**
  - **Validates: Requirements 12.3**

- [x] 9.4 Create tenant admin management page
  - Create /super-admin/tenants/{tenantId}/admins route
  - Display list of admins for selected tenant
  - Show username, email, created date
  - Add "Create Admin" button
  - Add edit/delete actions for each admin
  - _Requirements: 12.4_

- [x] 9.5 Create tenant admin creation form
  - Create modal/page for admin creation
  - Add form fields: username, password, email, tenant selection
  - Validate all required fields
  - Call POST /super-admin/tenants/{tenantId}/admins API
  - Show success/error messages
  - Refresh admin list on success
  - _Requirements: 12.5_

- [x] 9.6 Create tenant admin edit form
  - Create modal/page for admin editing
  - Pre-fill form with current admin data
  - Allow editing username, email, tenant assignment
  - Call PUT /super-admin/admins/{adminId} API
  - Show success/error messages
  - _Requirements: 13.1_

- [x] 10. Frontend - Tenant Admin Updates
  - Update admin interface to work with tenant context
  - _Requirements: 10.2_

- [x] 10.1 Update admin login page
  - Modify login form to handle tenant context in response
  - Store tenantId in localStorage along with token
  - Display tenant name after successful login
  - _Requirements: 9.4_

- [x] 10.2 Update session list page
  - Modify to display only sessions from admin's tenant
  - Remove tenant selection (automatic based on admin's tenant)
  - Update API calls to use tenant-filtered endpoints
  - _Requirements: 10.2_

- [x] 10.3 Update session creation page
  - Remove tenant selection field (automatic)
  - Session automatically associated with admin's tenant
  - Update API call to POST /admin/sessions
  - _Requirements: 10.1_

- [x] 11. Frontend - Participant Updates
  - Update participant interface for global registration
  - _Requirements: 1.1, 1.2, 2.1, 2.3, 11.1_

- [x] 11.1 Update participant registration page
  - Add tenantId to registration flow (from URL or QR code)
  - Check localStorage for existing global participantId
  - If exists, load profile from API
  - If not, show registration form
  - Call POST /participants/register with tenantId
  - Store participantId and token in localStorage
  - _Requirements: 1.1, 1.2, 2.1, 11.1_

- [x] 11.2 Update participant quiz view
  - Modify to auto-join session on load
  - Call POST /sessions/{sessionId}/join
  - Handle already-joined case (idempotent)
  - Display participant's global profile
  - _Requirements: 3.1_

- [x] 11.3 Create participant profile edit page
  - Create /profile route for participants
  - Display current name and avatar
  - Allow editing name and avatar
  - Call PUT /participants/{participantId}
  - Update localStorage with new profile
  - _Requirements: 2.3_

- [x] 12. Migration and Backward Compatibility
  - Create migration scripts and backward compatibility layer
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 12.1 Create default tenant setup script
  - Create script to initialize default tenant
  - Generate default tenant with name "Default Organization"
  - Set tenantId to a well-known UUID
  - Mark as active
  - Run during deployment if no tenants exist
  - _Requirements: 15.1_

- [x] 12.2 Create admin migration script
  - Create script to migrate existing admins to default tenant
  - Query all admins without tenantId
  - Update each admin to add default tenantId
  - Set role to tenant_admin (or super_admin for first admin)
  - Preserve all existing admin data
  - _Requirements: 15.2_

- [x] 12.3 Create session migration script
  - Create script to migrate existing sessions to default tenant
  - Query all sessions without tenantId
  - Update each session to add default tenantId
  - Preserve all existing session data
  - _Requirements: 15.3_

- [x] 12.4 Create participant migration script
  - Create script to migrate existing participants to global participants
  - Query all participants from old Participants table
  - Create GlobalParticipants records with default tenantId
  - Create SessionParticipations records linking participants to sessions
  - Migrate totalPoints and correctAnswers to SessionParticipations
  - Preserve all existing participant data
  - _Requirements: 15.4_

- [x] 12.5 Create answer migration script
  - Create script to add tenantId and participationId to existing answers
  - Query all answers
  - Look up session's tenantId
  - Look up participationId from SessionParticipations
  - Update answer records
  - _Requirements: 15.4_

- [x] 12.6 Implement backward compatibility layer
  - Add logic to handle requests without tenant context
  - Default to primary tenant if tenantId not provided
  - Support legacy token format (without tenantId)
  - Maintain existing API response formats
  - _Requirements: 6.4, 15.5_

- [x] 12.7 Write property test for API compatibility
  - **Property 21: API response format compatibility**
  - **Validates: Requirements 6.4**

- [x] 13. Testing and Validation
  - Implement comprehensive test suite
  - _Requirements: All_

- [x] 13.1 Implement all remaining property-based tests
  - Ensure all 44 correctness properties have corresponding tests
  - Configure Hypothesis with max_examples=100
  - Tag each test with property number and requirements
  - Run full property test suite

- [x] 13.2 Create integration test suite
  - Test complete tenant lifecycle
  - Test complete participant journey
  - Test cross-tenant isolation
  - Test migration scenarios
  - Test backward compatibility

- [x] 13.3 Create end-to-end test suite
  - Test super admin creates tenant and admin
  - Test tenant admin creates session
  - Test participant registers and joins session
  - Test participant submits answers and earns points
  - Test scoreboard displays correct data
  - Test cross-tenant access is blocked

- [x] 13.4 Perform security audit
  - Test authentication and authorization
  - Test tenant isolation
  - Test input validation
  - Test error handling
  - Test rate limiting

- [x] 13.5 Perform load testing
  - Test with multiple tenants
  - Test with many participants per tenant
  - Test concurrent session participation
  - Test database query performance
  - Verify GSI efficiency

- [x] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Documentation and Deployment
  - Create documentation and deploy the system
  - _Requirements: All_

- [x] 15.1 Update API documentation
  - Document all new endpoints
  - Document tenant context in authentication
  - Document error codes
  - Update request/response examples
  - _Requirements: All_

- [x] 15.2 Create deployment guide
  - Document deployment steps
  - Document migration process
  - Document rollback procedures
  - Document monitoring setup
  - _Requirements: All_

- [x] 15.3 Create admin user guide
  - Document super admin workflows
  - Document tenant admin workflows
  - Document tenant management
  - Document admin management
  - _Requirements: 8, 9, 10, 12, 13_

- [x] 15.4 Create participant user guide
  - Document registration process
  - Document profile management
  - Document session joining
  - Document quiz participation
  - _Requirements: 1, 2, 3, 11_

- [x] 15.5 Deploy to staging environment
  - Deploy updated CDK stack
  - Run migration scripts
  - Verify all endpoints work
  - Test with sample data
  - _Requirements: All_

- [x] 15.6 Deploy to production
  - Create database backup
  - Deploy updated CDK stack
  - Run migration scripts
  - Monitor for errors
  - Verify functionality
  - _Requirements: All_

- [ ] 16. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
