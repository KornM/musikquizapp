# Design Document: Multi-Tenant Global Participant Registration

## Overview

This design transforms the Music Quiz application from a single-tenant system with session-specific participants into a multi-tenant platform with global participant profiles. The system will support multiple organizations (tenants), each with their own administrators, participants, and quiz sessions, while maintaining complete data isolation between tenants.

### Key Design Goals

1. **Multi-Tenancy**: Support multiple independent organizations on a single platform
2. **Global Participants**: Participants register once per tenant and automatically join all sessions
3. **Data Isolation**: Complete separation of data between tenants
4. **Backward Compatibility**: Existing single-tenant deployments continue to work
5. **Scalability**: Design supports growth in tenants, participants, and sessions
6. **Security**: Strong authentication and authorization with tenant-aware access control

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Super Admin UI  │  Tenant Admin UI  │  Participant UI      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Lambda Functions                          │
├─────────────────────────────────────────────────────────────┤
│  Tenant Mgmt  │  Admin Auth  │  Participant  │  Session     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DynamoDB Tables                           │
├─────────────────────────────────────────────────────────────┤
│  Tenants  │  Admins  │  GlobalParticipants  │  Sessions    │
│  SessionParticipations  │  Rounds  │  Answers               │
└─────────────────────────────────────────────────────────────┘
```

### Tenant Isolation Strategy

All tenant-specific data will include a `tenantId` field. API operations will:
1. Extract tenant context from authenticated user
2. Filter all queries by `tenantId`
3. Validate cross-tenant access attempts
4. Enforce tenant boundaries at the database query level

## Components and Interfaces

### 1. Tenant Management Service

**Responsibilities:**
- Create, read, update, delete tenants
- Manage tenant lifecycle and status
- Provide tenant lookup and validation

**API Endpoints:**

```
POST   /super-admin/tenants              - Create tenant
GET    /super-admin/tenants              - List all tenants
GET    /super-admin/tenants/{tenantId}   - Get tenant details
PUT    /super-admin/tenants/{tenantId}   - Update tenant
DELETE /super-admin/tenants/{tenantId}   - Delete/deactivate tenant
```

### 2. Tenant Admin Management Service

**Responsibilities:**
- Create, read, update, delete tenant administrators
- Associate admins with tenants
- Manage admin credentials and permissions

**API Endpoints:**

```
POST   /super-admin/tenants/{tenantId}/admins           - Create tenant admin
GET    /super-admin/tenants/{tenantId}/admins           - List tenant admins
GET    /super-admin/admins/{adminId}                    - Get admin details
PUT    /super-admin/admins/{adminId}                    - Update admin
DELETE /super-admin/admins/{adminId}                    - Delete admin
POST   /super-admin/admins/{adminId}/reset-password     - Reset admin password
```

### 3. Enhanced Admin Authentication Service

**Responsibilities:**
- Authenticate admin users
- Return JWT tokens with tenant context
- Differentiate between super admins and tenant admins

**API Endpoints:**

```
POST   /admin/login                      - Admin login (returns token with tenantId)
POST   /admin/logout                     - Admin logout
GET    /admin/me                         - Get current admin info
```

**Token Payload:**
```json
{
  "adminId": "uuid",
  "tenantId": "uuid",
  "role": "admin" | "super_admin",
  "exp": 1234567890
}
```

### 4. Global Participant Service

**Responsibilities:**
- Create and manage global participant profiles
- Handle participant authentication
- Manage participant-tenant associations

**API Endpoints:**

```
POST   /participants/register            - Register global participant
GET    /participants/{participantId}     - Get participant profile
PUT    /participants/{participantId}     - Update participant profile
GET    /participants/me                  - Get current participant info
```

### 5. Session Participation Service

**Responsibilities:**
- Auto-register participants for sessions
- Track session-specific participation
- Manage session scores and answers

**API Endpoints:**

```
POST   /sessions/{sessionId}/join        - Join session (auto-creates participation)
GET    /sessions/{sessionId}/participants - Get session participants
GET    /participants/{participantId}/sessions - Get participant's sessions
```

### 6. Enhanced Session Management Service

**Responsibilities:**
- Create and manage sessions with tenant context
- Filter sessions by tenant
- Enforce tenant isolation

**Modified API Endpoints:**

```
POST   /admin/sessions                   - Create session (auto-adds tenantId)
GET    /admin/sessions                   - List sessions (filtered by tenantId)
GET    /admin/sessions/{sessionId}       - Get session (validates tenantId)
```

## Data Models

### Tenants Table

```
Table: Tenants
Primary Key: tenantId (String)

Attributes:
- tenantId: String (UUID)
- name: String
- description: String (optional)
- status: String (active | inactive)
- createdAt: String (ISO timestamp)
- updatedAt: String (ISO timestamp)
- settings: Map (tenant-specific configuration)

GSI: StatusIndex
- Partition Key: status
- Sort Key: createdAt
```

### Admins Table (Enhanced)

```
Table: Admins
Primary Key: adminId (String)

Attributes:
- adminId: String (UUID)
- tenantId: String (UUID) - NULL for super admins
- username: String
- passwordHash: String
- role: String (super_admin | tenant_admin)
- email: String (optional)
- createdAt: String (ISO timestamp)
- updatedAt: String (ISO timestamp)

GSI: UsernameIndex (existing)
- Partition Key: username

GSI: TenantIndex (new)
- Partition Key: tenantId
- Sort Key: createdAt
```

### GlobalParticipants Table (New)

```
Table: GlobalParticipants
Primary Key: participantId (String)

Attributes:
- participantId: String (UUID)
- tenantId: String (UUID)
- name: String
- avatar: String (emoji)
- token: String (JWT)
- createdAt: String (ISO timestamp)
- updatedAt: String (ISO timestamp)

GSI: TenantIndex
- Partition Key: tenantId
- Sort Key: createdAt
```

### SessionParticipations Table (New)

```
Table: SessionParticipations
Primary Key: participationId (String)

Attributes:
- participationId: String (UUID)
- participantId: String (UUID) - FK to GlobalParticipants
- sessionId: String (UUID) - FK to QuizSessions
- tenantId: String (UUID) - Denormalized for filtering
- joinedAt: String (ISO timestamp)
- totalPoints: Number (default: 0)
- correctAnswers: Number (default: 0)

GSI: SessionIndex
- Partition Key: sessionId
- Sort Key: joinedAt

GSI: ParticipantIndex
- Partition Key: participantId
- Sort Key: joinedAt
```

### QuizSessions Table (Enhanced)

```
Table: QuizSessions
Primary Key: sessionId (String)

Attributes:
- sessionId: String (UUID)
- tenantId: String (UUID) - NEW
- title: String
- description: String
- status: String
- currentRound: Number
- roundCount: Number
- createdAt: String (ISO timestamp)
- ... (other existing fields)

GSI: TenantStatusIndex (new)
- Partition Key: tenantId
- Sort Key: createdAt
```

### Answers Table (Enhanced)

```
Table: Answers
Primary Key: answerId (String)

Attributes:
- answerId: String (UUID)
- participantId: String (UUID) - Now references GlobalParticipants
- participationId: String (UUID) - FK to SessionParticipations
- sessionId: String (UUID)
- tenantId: String (UUID) - Denormalized for filtering
- roundNumber: Number
- answer: Number
- isCorrect: Boolean
- points: Number
- submittedAt: String (ISO timestamp)

(Existing GSIs remain the same)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Global participant creation generates unique ID
*For any* participant registration request, the system should create a global participant record with a unique participant ID that doesn't collide with existing IDs.
**Validates: Requirements 1.1, 7.1**

### Property 2: Participant profile storage
*For any* name and avatar combination provided during registration, the system should store these values in the global participant profile and return them unchanged when retrieved.
**Validates: Requirements 1.2**

### Property 3: Profile independence from sessions
*For any* global participant created, the participant record should exist in the GlobalParticipants table without any session reference (sessionId field should not exist in the participant record).
**Validates: Requirements 1.3**

### Property 4: Authentication token generation
*For any* global participant creation, the system should generate a valid JWT token and include it in the response.
**Validates: Requirements 1.4**

### Property 5: Participant ID in response
*For any* participant registration, the API response should contain the global participant ID.
**Validates: Requirements 1.5**

### Property 6: Profile retrieval
*For any* existing global participant ID, querying the system should return the participant's profile with matching name and avatar.
**Validates: Requirements 2.1**

### Property 7: Profile update persistence
*For any* global participant profile update with new name or avatar, the updated values should be stored in the database and returned in subsequent queries.
**Validates: Requirements 2.3**

### Property 8: Profile updates propagate to sessions
*For any* global participant who updates their profile and then joins a new session, the session participation should reflect the updated profile information.
**Validates: Requirements 2.4**

### Property 9: Auto-creation of session participation
*For any* global participant joining any session, the system should automatically create a session participation record linking the participant ID and session ID.
**Validates: Requirements 3.1**

### Property 10: Participation record linkage
*For any* session participation record, it should contain both a valid participantId (referencing GlobalParticipants) and a valid sessionId (referencing QuizSessions).
**Validates: Requirements 3.2**

### Property 11: Initial score is zero
*For any* new session participation created, the totalPoints field should be initialized to 0.
**Validates: Requirements 3.3**

### Property 12: Join timestamp recording
*For any* session participation created, the joinedAt field should contain a valid timestamp representing when the participant joined.
**Validates: Requirements 3.4**

### Property 13: Complete participant list for session
*For any* session, querying the participant list should return all participants who have joined that session (all SessionParticipations records for that sessionId).
**Validates: Requirements 4.1**

### Property 14: Participant list contains required fields
*For any* participant in a session participant list, the response should include the participant's name, avatar, and current score (totalPoints).
**Validates: Requirements 4.2**

### Property 15: Participant list reflects current profile
*For any* participant who updates their global profile, subsequent queries to session participant lists should show the updated name and avatar.
**Validates: Requirements 4.3, 4.5**

### Property 16: Answer linked to participation
*For any* answer submitted by a participant, the answer record should reference the correct participationId from SessionParticipations.
**Validates: Requirements 5.1**

### Property 17: Score isolation per session
*For any* participant who joins multiple sessions and earns points in each, the totalPoints in each SessionParticipation record should be independent and reflect only that session's score.
**Validates: Requirements 5.2**

### Property 18: Independent participation records
*For any* participant joining N sessions, the system should create N distinct SessionParticipation records, each with a unique participationId.
**Validates: Requirements 5.3**

### Property 19: Scoreboard session specificity
*For any* session scoreboard query, the returned scores should only include participants from that specific session (filtered by sessionId).
**Validates: Requirements 5.4**

### Property 20: Score and answer persistence
*For any* session that ends, the SessionParticipation records and Answer records for that session should remain unchanged and queryable.
**Validates: Requirements 5.5**

### Property 21: API response format compatibility
*For any* API endpoint, the response format should match the documented schema with all required fields present.
**Validates: Requirements 6.4**

### Property 22: Unauthorized access denial
*For any* request to access a participant profile with an invalid or missing authentication token, the system should return a 401 Unauthorized error.
**Validates: Requirements 7.3, 7.4**

### Property 23: Token contains participant ID
*For any* participant authentication token generated, decoding the JWT should reveal a payload containing the global participant ID.
**Validates: Requirements 7.5**

### Property 24: Unique tenant ID generation
*For any* tenant creation request, the system should generate a unique tenant ID that doesn't collide with existing tenant IDs.
**Validates: Requirements 8.1**

### Property 25: Tenant creation validation
*For any* tenant creation request without a name, the system should reject the request; requests with a name and optional description should succeed.
**Validates: Requirements 8.2**

### Property 26: Tenant list completeness
*For any* super admin query for tenants, the response should include all tenants with their names, creation dates (createdAt), and status fields.
**Validates: Requirements 8.4**

### Property 27: Tenant deletion blocks new sessions
*For any* tenant marked as inactive/deleted, attempts to create new sessions for that tenant should be rejected.
**Validates: Requirements 8.5**

### Property 28: Tenant admin association
*For any* tenant admin created, the admin record should contain a tenantId field referencing a valid tenant.
**Validates: Requirements 9.1**

### Property 29: Tenant admin creation validation
*For any* tenant admin creation request, the system should require username, password, and tenantId; missing any field should result in rejection.
**Validates: Requirements 9.2**

### Property 30: Admin login returns tenant context
*For any* tenant admin login, the response should include the admin's tenantId.
**Validates: Requirements 9.4**

### Property 31: Session inherits admin tenant
*For any* session created by a tenant admin, the session record should contain the same tenantId as the admin who created it.
**Validates: Requirements 10.1**

### Property 32: Session list tenant filtering
*For any* tenant admin querying sessions, the results should only include sessions where the session's tenantId matches the admin's tenantId.
**Validates: Requirements 10.2, 10.4**

### Property 33: Cross-tenant session access denial
*For any* tenant admin attempting to access a session with a different tenantId than their own, the system should deny access with a 403 Forbidden error.
**Validates: Requirements 10.3, 14.4**

### Property 34: Participant tenant association
*For any* participant registration, the participant record should contain a tenantId field.
**Validates: Requirements 11.1**

### Property 35: Cross-tenant session join denial
*For any* participant attempting to join a session where the session's tenantId differs from the participant's tenantId, the system should deny access.
**Validates: Requirements 11.2, 11.3**

### Property 36: Participant list tenant filtering
*For any* session participant list, all participants should have the same tenantId as the session.
**Validates: Requirements 11.4**

### Property 37: Tenant form submission creates tenant
*For any* valid tenant creation form submission (with name), the system should create a new tenant record in the database.
**Validates: Requirements 12.3**

### Property 38: Admin update persistence
*For any* tenant admin update request, the changes should be saved to the database and reflected in subsequent queries.
**Validates: Requirements 13.2**

### Property 39: Admin deletion blocks access
*For any* tenant admin that is deleted, subsequent login attempts with that admin's credentials should fail.
**Validates: Requirements 13.3**

### Property 40: Password change effectiveness
*For any* tenant admin password change, the admin should be able to login with the new password and unable to login with the old password.
**Validates: Requirements 13.4**

### Property 41: Admin tenant reassignment
*For any* tenant admin reassigned to a different tenant, the admin's tenantId should be updated and they should only see data from the new tenant.
**Validates: Requirements 13.5**

### Property 42: Query tenant isolation
*For any* database query for tenant-specific data, the results should only include records matching the authenticated user's tenantId.
**Validates: Requirements 14.2**

### Property 43: Tenant deletion cascades
*For any* tenant deletion, all associated sessions, participants, and participations should be deleted or marked as inactive.
**Validates: Requirements 14.3**

### Property 44: Participant deletion cascades
*For any* global participant deletion, all associated SessionParticipation records should be deleted or marked as inactive.
**Validates: Requirements 16.4**

## Error Handling

### Error Response Format

All errors will follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Error Codes

**Authentication & Authorization:**
- `MISSING_TOKEN` (401): Authorization header missing
- `INVALID_TOKEN` (401): JWT token is invalid or expired
- `INSUFFICIENT_PERMISSIONS` (403): User lacks required permissions
- `CROSS_TENANT_ACCESS` (403): Attempted to access another tenant's data

**Validation:**
- `INVALID_REQUEST` (400): Request body is missing or malformed
- `INVALID_JSON` (400): Request body is not valid JSON
- `MISSING_FIELDS` (400): Required fields are missing
- `INVALID_FIELD_VALUE` (400): Field value doesn't meet requirements

**Resource Not Found:**
- `TENANT_NOT_FOUND` (404): Tenant doesn't exist
- `ADMIN_NOT_FOUND` (404): Admin doesn't exist
- `PARTICIPANT_NOT_FOUND` (404): Participant doesn't exist
- `SESSION_NOT_FOUND` (404): Session doesn't exist

**Business Logic:**
- `TENANT_INACTIVE` (400): Tenant is inactive/deleted
- `DUPLICATE_USERNAME` (409): Username already exists
- `INVALID_TENANT_ASSIGNMENT` (400): Invalid tenant ID provided

**System:**
- `DATABASE_ERROR` (500): Database operation failed
- `INTERNAL_ERROR` (500): Unexpected system error

### Error Handling Strategy

1. **Input Validation**: Validate all inputs before processing
2. **Early Returns**: Return errors as soon as they're detected
3. **Consistent Format**: Use standard error response format
4. **Logging**: Log all errors with context for debugging
5. **User-Friendly Messages**: Provide clear, actionable error messages
6. **Security**: Don't expose sensitive information in error messages

## Testing Strategy

### Unit Testing

Unit tests will verify individual functions and components:

**Tenant Management:**
- Tenant CRUD operations
- Tenant validation logic
- Tenant status management

**Admin Management:**
- Admin CRUD operations
- Password hashing and verification
- Tenant assignment logic

**Participant Management:**
- Global participant creation
- Profile updates
- Participant-tenant association

**Session Participation:**
- Auto-registration logic
- Score calculation
- Participation record management

**Authorization:**
- Token generation and validation
- Tenant isolation checks
- Permission verification

### Property-Based Testing

Property-based tests will verify universal properties across all inputs using **Hypothesis** (Python property-based testing library). Each property test will run a minimum of 100 iterations with randomly generated data.

**Test Configuration:**
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(
    name=st.text(min_size=1, max_size=100),
    avatar=st.text(min_size=1, max_size=10)
)
def test_property_participant_profile_storage(name, avatar):
    # Test implementation
    pass
```

**Property Test Organization:**
- Each correctness property will be implemented as a separate property-based test
- Tests will be tagged with comments referencing the design document property number
- Tests will use Hypothesis strategies to generate valid test data
- Tests will verify properties hold across all generated inputs

**Example Property Test:**
```python
@settings(max_examples=100)
@given(
    participant_data=st.fixed_dictionaries({
        'name': st.text(min_size=1, max_size=100),
        'avatar': st.sampled_from(['😀', '😎', '🤓', '🥳']),
        'tenantId': st.uuids()
    })
)
def test_property_2_participant_profile_storage(participant_data):
    """
    Feature: global-participant-registration, Property 2: Participant profile storage
    
    For any name and avatar combination provided during registration,
    the system should store these values in the global participant profile
    and return them unchanged when retrieved.
    """
    # Create participant
    response = create_participant(
        name=participant_data['name'],
        avatar=participant_data['avatar'],
        tenant_id=str(participant_data['tenantId'])
    )
    
    participant_id = response['participantId']
    
    # Retrieve participant
    retrieved = get_participant(participant_id)
    
    # Verify stored values match input
    assert retrieved['name'] == participant_data['name']
    assert retrieved['avatar'] == participant_data['avatar']
```

### Integration Testing

Integration tests will verify end-to-end workflows:

**Tenant Lifecycle:**
1. Super admin creates tenant
2. Super admin creates tenant admin
3. Tenant admin logs in
4. Tenant admin creates session
5. Verify tenant isolation

**Participant Journey:**
1. Participant registers for tenant
2. Participant joins session
3. Participant submits answers
4. Verify scores are tracked
5. Participant joins another session
6. Verify independent scores

**Cross-Tenant Isolation:**
1. Create two tenants with admins
2. Create sessions in each tenant
3. Verify admins can't access other tenant's sessions
4. Create participants in each tenant
5. Verify participants can't join other tenant's sessions

### Migration Testing

Tests for backward compatibility:

1. **Legacy Data Support**: Verify system handles existing participant records
2. **Default Tenant**: Verify single-tenant mode works without tenant configuration
3. **Token Compatibility**: Verify both old and new token formats work
4. **API Compatibility**: Verify existing API clients continue to work

## Implementation Phases

### Phase 1: Database Schema Updates
- Create Tenants table
- Create GlobalParticipants table
- Create SessionParticipations table
- Add tenantId to Admins table
- Add tenantId to QuizSessions table
- Add tenantId to Answers table
- Create necessary GSIs

### Phase 2: Tenant Management
- Implement tenant CRUD operations
- Create super admin management interface
- Implement tenant admin management
- Add tenant validation middleware

### Phase 3: Global Participant System
- Implement global participant registration
- Implement profile management
- Update authentication to use global participants
- Implement auto-registration for sessions

### Phase 4: Tenant Isolation
- Add tenant filtering to all queries
- Implement cross-tenant access checks
- Update admin authentication to include tenant context
- Add tenant validation to all APIs

### Phase 5: Frontend Updates
- Create super admin UI for tenant management
- Update admin login to handle tenant context
- Update participant registration for global profiles
- Update session views to show tenant-filtered data

### Phase 6: Migration & Backward Compatibility
- Create migration scripts for existing data
- Implement default tenant for single-tenant mode
- Add backward compatibility layer
- Test with existing deployments

### Phase 7: Testing & Validation
- Implement all property-based tests
- Run integration tests
- Perform security audit
- Load testing for multi-tenant scenarios

## Security Considerations

### Authentication
- JWT tokens include tenant context
- Tokens are validated on every request
- Token expiration enforced (24 hours)
- Passwords hashed using bcrypt

### Authorization
- Role-based access control (super admin vs tenant admin)
- Tenant isolation enforced at query level
- Cross-tenant access attempts logged and blocked
- Participant access limited to their tenant

### Data Isolation
- All tenant-specific queries filtered by tenantId
- Database-level tenant ID validation
- No shared data between tenants
- Tenant deletion cascades properly

### Input Validation
- All inputs sanitized and validated
- SQL injection prevention (using DynamoDB)
- XSS prevention in frontend
- Rate limiting on authentication endpoints

## Performance Considerations

### Database Optimization
- GSIs for efficient tenant-based queries
- Composite keys for session participations
- Denormalized tenantId for faster filtering
- Batch operations for bulk updates

### Caching Strategy
- Cache tenant information (rarely changes)
- Cache global participant profiles
- Invalidate cache on profile updates
- Use DynamoDB DAX for hot data

### Scalability
- Stateless Lambda functions
- DynamoDB auto-scaling
- CloudFront for frontend distribution
- API Gateway throttling per tenant

## Monitoring & Observability

### Metrics
- Tenant creation rate
- Participant registration rate per tenant
- Session participation rate
- Cross-tenant access attempts (security metric)
- API latency per tenant
- Error rates by error code

### Logging
- All tenant operations logged
- Authentication attempts logged
- Cross-tenant access attempts logged
- Error details with context
- Performance metrics

### Alerts
- High error rates
- Cross-tenant access attempts
- Authentication failures
- Database performance issues
- Lambda function errors

## Deployment Strategy

### Blue-Green Deployment
1. Deploy new Lambda functions alongside existing ones
2. Update API Gateway to route to new functions
3. Monitor for errors
4. Rollback if issues detected
5. Decommission old functions after validation

### Database Migration
1. Create new tables (Tenants, GlobalParticipants, SessionParticipations)
2. Add tenantId columns to existing tables
3. Run migration script to populate default tenant
4. Migrate existing participants to global participants
5. Validate data integrity
6. Switch to new system

### Rollback Plan
1. Keep old Lambda functions available
2. Maintain database backups before migration
3. API Gateway can route back to old functions
4. Document rollback procedures
5. Test rollback in staging environment
