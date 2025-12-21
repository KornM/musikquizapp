# Multi-Tenant Migration Scripts

This directory contains scripts for migrating the Music Quiz application from single-tenant to multi-tenant architecture, as well as setup scripts for initial deployment.

## Overview

The migration process transforms the application to support multiple organizations (tenants) while maintaining backward compatibility with existing data.

## Setup Scripts

### `create_super_admin.py`
Creates a super admin user with full system access.

**Usage:**
```bash
python scripts/create_super_admin.py \
  --username superadmin \
  --password "SecurePassword123!" \
  --email admin@example.com
```

**Arguments:**
- `--username` (required): Super admin username
- `--password` (required): Super admin password (min 8 characters)
- `--email` (optional): Super admin email address
- `--table-name` (optional): DynamoDB table name (default: Admins)

**Features:**
- Automatically sets role to "super_admin"
- Omits tenantId (super admins are not tenant-specific)
- Validates username and password requirements
- Checks for existing username conflicts

**When to use:**
- Initial deployment to create the first super admin
- Adding additional super admin users

### `create_admin.py`
Creates a basic admin user (legacy script).

**Usage:**
```bash
python scripts/create_admin.py \
  --username admin \
  --password "SecurePassword123!"
```

**Note:** This script creates a basic admin without role or tenant assignment. For super admins, use `create_super_admin.py` instead. For tenant admins, use the API or super admin UI.

## Migration Scripts

### 1. `setup_default_tenant.py`
Creates a default tenant for backward compatibility with single-tenant deployments.

**Usage:**
```bash
python scripts/setup_default_tenant.py
python scripts/setup_default_tenant.py --force  # Create even if tenants exist
```

**What it does:**
- Creates a tenant with ID `00000000-0000-0000-0000-000000000001`
- Names it "Default Organization"
- Sets status to "active"
- Skips if tenants already exist (unless --force is used)

### 2. `migrate_admins.py`
Migrates existing admin users to the multi-tenant model.

**Usage:**
```bash
python scripts/migrate_admins.py
python scripts/migrate_admins.py --dry-run  # Preview changes
```

**What it does:**
- Finds all admins without a tenantId
- Makes the first admin (by creation date) a super_admin
- Makes subsequent admins tenant_admins for the default tenant
- Preserves all existing admin data

### 3. `migrate_sessions.py`
Migrates existing quiz sessions to the multi-tenant model.

**Usage:**
```bash
python scripts/migrate_sessions.py
python scripts/migrate_sessions.py --dry-run  # Preview changes
```

**What it does:**
- Finds all sessions without a tenantId
- Associates them with the default tenant
- Preserves all existing session data

### 4. `migrate_participants.py`
Migrates session-specific participants to global participants.

**Usage:**
```bash
python scripts/migrate_participants.py
python scripts/migrate_participants.py --dry-run  # Preview changes
```

**What it does:**
- Reads participants from the legacy Participants table
- Creates GlobalParticipants records with default tenant
- Creates SessionParticipations records linking participants to sessions
- Migrates totalPoints and correctAnswers to SessionParticipations
- Preserves all existing participant data

### 5. `migrate_answers.py`
Adds tenant context to existing answers.

**Usage:**
```bash
python scripts/migrate_answers.py
python scripts/migrate_answers.py --dry-run  # Preview changes
```

**What it does:**
- Finds all answers without tenantId
- Looks up the session's tenantId
- Looks up the participationId from SessionParticipations
- Updates answer records with tenantId and participationId

### 6. `run_full_migration.py`
Orchestrates the complete migration process.

**Usage:**
```bash
python scripts/run_full_migration.py
python scripts/run_full_migration.py --dry-run  # Preview all changes
python scripts/run_full_migration.py --skip-tenant-setup  # Skip step 1
```

**What it does:**
- Runs all migration scripts in the correct order
- Provides progress feedback
- Stops if any step fails
- Supports dry-run mode for testing

## Migration Process

### Prerequisites

1. **Backup your database** before running any migration scripts
2. Ensure you have AWS credentials configured
3. Ensure the CDK stack has been deployed with the new tables:
   - Tenants
   - GlobalParticipants
   - SessionParticipations

### Step-by-Step Migration

#### Option A: Full Automated Migration (Recommended)

```bash
# 1. Test the migration (dry-run)
python scripts/run_full_migration.py --dry-run

# 2. Review the output and verify it looks correct

# 3. Run the actual migration
python scripts/run_full_migration.py
```

#### Option B: Manual Step-by-Step Migration

```bash
# 1. Create default tenant
python scripts/setup_default_tenant.py

# 2. Migrate admins
python scripts/migrate_admins.py --dry-run  # Preview
python scripts/migrate_admins.py            # Execute

# 3. Migrate sessions
python scripts/migrate_sessions.py --dry-run  # Preview
python scripts/migrate_sessions.py            # Execute

# 4. Migrate participants
python scripts/migrate_participants.py --dry-run  # Preview
python scripts/migrate_participants.py            # Execute

# 5. Migrate answers
python scripts/migrate_answers.py --dry-run  # Preview
python scripts/migrate_answers.py            # Execute
```

### Verification

After migration, verify the following:

1. **Default tenant exists:**
   ```bash
   aws dynamodb get-item \
     --table-name Tenants \
     --key '{"tenantId": {"S": "00000000-0000-0000-0000-000000000001"}}'
   ```

2. **Admins have tenantId and role:**
   ```bash
   aws dynamodb scan --table-name Admins --max-items 5
   ```

3. **Sessions have tenantId:**
   ```bash
   aws dynamodb scan --table-name QuizSessions --max-items 5
   ```

4. **Global participants exist:**
   ```bash
   aws dynamodb scan --table-name GlobalParticipants --max-items 5
   ```

5. **Session participations exist:**
   ```bash
   aws dynamodb scan --table-name SessionParticipations --max-items 5
   ```

6. **Answers have tenantId and participationId:**
   ```bash
   aws dynamodb scan --table-name Answers --max-items 5
   ```

### Rollback

If you need to rollback:

1. Restore from your database backup
2. Redeploy the previous CDK stack version
3. Redeploy the previous Lambda functions

## Backward Compatibility

The migration maintains backward compatibility:

- **Legacy tokens:** Tokens without tenantId are accepted and default to the primary tenant
- **API responses:** Maintain the same format as before
- **Single-tenant mode:** If only the default tenant exists, the system operates like before
- **Existing data:** All existing data is preserved and accessible

## Troubleshooting

### "No tenants found that need migration"
This is normal if you've already run the migration. Use `--force` flag if you need to recreate the default tenant.

### "Could not find participationId"
This can happen if participants were migrated but answers reference participants that don't exist. Check your data integrity.

### "TypeError: '<' not supported between instances of 'str' and 'decimal.Decimal'"
This error occurs when admins have mixed timestamp formats (some ISO strings, some Unix timestamps). This has been fixed in the latest version of `migrate_admins.py`. Update your script and try again.

**Solution:**
```bash
# Pull the latest version of the migration scripts
git pull origin main

# Or manually update migrate_admins.py with the fixed sorting logic
```

### "ValidationException: Schema violation against backfilling index"
This error occurs when trying to add a `tenantId` to an admin that has `createdAt` in the wrong format (Decimal instead of String). The TenantIndex GSI requires both `tenantId` (partition key) and `createdAt` (sort key) to be strings.

**Root Cause:**
- Old admins created with legacy scripts had `createdAt` as Unix timestamp (Decimal)
- The TenantIndex GSI expects `createdAt` as a String (ISO format)
- When adding `tenantId`, DynamoDB tries to backfill the GSI and fails due to type mismatch

**Solution:**
The latest version of `migrate_admins.py` automatically converts `createdAt` to ISO string format during migration. Update your script and try again:

```bash
# Pull the latest version
git pull origin main

# Run migration again
python3 scripts/migrate_admins.py
```

### Migration script hangs or times out
If migration scripts take too long:
- Check your internet connection
- Verify AWS credentials are valid
- Check DynamoDB table capacity
- Consider running migrations in smaller batches

### "Admin already has tenantId"
This means the admin has already been migrated. The script skips already-migrated admins automatically.

### "Error checking existing user"
Ensure your AWS credentials are configured correctly and you have permissions to access DynamoDB.

### Migration fails partway through
The scripts are idempotent - you can safely re-run them. Already migrated items will be skipped.

## Support

For issues or questions:
1. Check the script output for detailed error messages
2. Review the CloudWatch logs for Lambda functions
3. Verify your AWS credentials and permissions
4. Ensure the CDK stack is deployed correctly

## Default Tenant ID

The default tenant uses a well-known UUID:
```
00000000-0000-0000-0000-000000000001
```

This ID is consistent across all migration scripts and the backward compatibility layer.
