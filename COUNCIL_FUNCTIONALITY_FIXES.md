# Council Functionality Fixes - Production Deployment

**Date**: January 28, 2026  
**Environment**: Production (accordant.eu)  
**Database**: PostgreSQL (ai-stack_db)  
**Related Repo**: xmarkdigest

## Executive Summary

During testing of the Accordant council functionality, several critical issues were identified and resolved:

1. **Database Schema Mismatch**: Missing `isGrounded` and `personaIds` columns in `CouncilRun` table
2. **Model Name Format Issues**: Incorrect Anthropic model names causing LiteLLM API failures
3. **Persona Form UI Bug**: Model field not updating after save
4. **Deprecated Browser Header**: Permissions-Policy header using deprecated `interest-cohort` feature

All issues have been resolved and the council functionality is now operational.

---

## Issues Encountered and Fixes Applied

### 1. Database Schema Mismatch - Missing Columns in CouncilRun Table

**Issue**:  
Prisma client was failing with error:
```
Invalid `prisma.councilRun.create()` invocation:
The column `isGrounded` does not exist in the current database.
```

**Root Cause**:  
- The Prisma schema (`packages/database/prisma/schema.prisma`) defined `isGrounded` and `personaIds` columns
- The database migration (`20260122000149_refine_council_run/migration.sql`) did not include these columns
- Prisma client was generated with schema that didn't match the actual database structure

**Fix Applied**:  
1. Added missing columns directly to the database:
   ```sql
   ALTER TABLE "CouncilRun" 
   ADD COLUMN IF NOT EXISTS "isGrounded" BOOLEAN NOT NULL DEFAULT false;
   
   ALTER TABLE "CouncilRun" 
   ADD COLUMN IF NOT EXISTS "personaIds" TEXT[] DEFAULT ARRAY[]::TEXT[];
   ```

2. Rebuilt the Docker container to regenerate Prisma client:
   ```bash
   docker build --no-cache -f xmarkdigest/Dockerfile --target web -t accordant-web:latest xmarkdigest
   docker restart ai-stack_accordant_web
   ```

**Verification**:  
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'CouncilRun' 
AND column_name IN ('isGrounded', 'personaIds');
-- Returns: isGrounded, personaIds
```

**Recommendation for xmarkdigest repo**:  
- Update migration `20260122000149_refine_council_run/migration.sql` to include these columns:
  ```sql
  ADD COLUMN "isGrounded" BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN "personaIds" TEXT[] DEFAULT ARRAY[]::TEXT[];
  ```
- Ensure all schema changes are reflected in migrations before deployment
- Consider adding a migration validation step in CI/CD pipeline

**Files Modified**:  
- `packages/database/prisma/migrations/20260122000149_refine_council_run/migration.sql` - Added missing columns
- Container: Rebuilt to regenerate Prisma client

**Commit**: `00acda4` - fix(database): add missing isGrounded and personaIds columns to CouncilRun migration

---

### 2. Model Name Format Issues - Anthropic Models Not Recognized by LiteLLM

**Issue**:  
LiteLLM API was rejecting requests with error:
```
litellm.NotFoundError: AnthropicException - {"type":"error","error":{"type":"not_found_error","message":"model: claude-3-5-sonnet"},"request_id":"..."}
Received Model Group=anthropic/claude-3-5-sonnet
Available Model Group Fallbacks=None
```

**Root Cause**:  
- Persona YAML files and database records used model name `anthropic/claude-3-5-sonnet`
- LiteLLM requires the full model identifier with date suffix: `anthropic/claude-3-5-sonnet-20241022`
- Missing date suffix caused model lookup failures

**Fix Applied**:  
1. Updated all Anthropic persona YAML files:
   - `packages/council/resources/personalities/anthropic_council_systems_strategist.yaml`
   - `packages/council/resources/personalities/anthropic_council_operational_pragmatist.yaml`
   - `packages/council/resources/personalities/anthropic_council_underlying_principles_analyst.yaml`
   - `packages/council/resources/personalities/anthropic_council_adversarial_critic.yaml`
   
   Changed from:
   ```yaml
   model: anthropic/claude-3-5-sonnet
   ```
   To:
   ```yaml
   model: anthropic/claude-3-5-sonnet-20241022
   ```

2. Updated database records:
   ```sql
   UPDATE "CouncilPersona" 
   SET model = 'anthropic/claude-3-5-sonnet-20241022' 
   WHERE model = 'anthropic/claude-3-5-sonnet';
   ```

**Verification**:  
```sql
SELECT id, name, model FROM "CouncilPersona" WHERE id LIKE 'anthropic_%';
-- All Anthropic personas now use: anthropic/claude-3-5-sonnet-20241022
```

**Recommendation for xmarkdigest repo**:  
- Update all persona YAML files with correct model identifiers including date suffixes
- Document model naming conventions for LiteLLM compatibility
- Consider adding validation in seed scripts to ensure model names match LiteLLM format
- Update seed script (`packages/database/scripts/seed-council.ts`) to use correct model names

**Files Modified**:  
- `packages/council/resources/personalities/anthropic_council_*.yaml` (4 files)
- Database: `CouncilPersona` table (4 records updated)

**Commit**: `1f20f14` - fix(council): update Anthropic model names to include date suffix

---

### 3. Persona Form UI Bug - Model Field Not Updating After Save

**Issue**:  
When editing a persona and changing the model dropdown, the change was saved to the database but the form didn't reflect the updated value after save/redirect.

**Root Cause**:  
- React form used `defaultValue` prop on the select element
- After form submission and redirect, React didn't re-render the select with the new value
- Missing `key` prop prevented React from detecting when the persona data changed

**Fix Applied**:  
Added `key` prop to the model select element to force React re-render:

```tsx
// File: apps/web/components/admin/council/persona-form.tsx
<select
    className="..."
    id="model"
    name="model"
    key={persona?.id || 'new'}  // Added key prop
    defaultValue={persona?.model || 'anthropic/claude-3-sonnet-20240229'}
>
```

**Recommendation for xmarkdigest repo**:  
- Consider using controlled components (`value` + `onChange`) instead of `defaultValue` for better state management
- Ensure form components properly handle data updates after server actions
- Add form validation feedback to confirm successful saves

**Files Modified**:  
- `apps/web/components/admin/council/persona-form.tsx`

**Commit**: `b330187` - fix(ui): add key prop to persona model select for proper re-rendering

---

### 4. Deprecated Browser Header - Permissions-Policy Warning

**Issue**:  
Browser console showing warning:
```
Error with Permissions-Policy header: Unrecognized feature: 'interest-cohort'.
```

**Root Cause**:  
- Traefik security headers middleware included deprecated `interest-cohort` feature
- This feature was part of Google's FLoC (Federated Learning of Cohorts) proposal, which has been deprecated

**Fix Applied**:  
Removed `interest-cohort=()` from Permissions-Policy header:

```yaml
# File: /root/ai-stack/config/traefik/dynamic/security-headers.yml
# Before:
Permissions-Policy: "camera=(), microphone=(), geolocation=(), interest-cohort=()"

# After:
Permissions-Policy: "camera=(), microphone=(), geolocation=()"
```

Restarted Traefik to apply changes:
```bash
docker-compose restart traefik
```

**Recommendation for xmarkdigest repo**:  
- This fix is in the ai-stack infrastructure repo, not xmarkdigest
- If xmarkdigest has its own security headers configuration, ensure it doesn't include deprecated features
- Regularly review browser compatibility for security headers

**Files Modified**:  
- `/root/ai-stack/config/traefik/dynamic/security-headers.yml` (infrastructure repo)

---

## Testing Results

After applying all fixes:

✅ **Database Schema**: All columns exist and Prisma client recognizes them  
✅ **Model Names**: Anthropic models now use correct format with date suffixes  
✅ **Persona Form**: Model field updates correctly after save  
✅ **Browser Headers**: No more console warnings about deprecated features  
✅ **Council Functionality**: Successfully processing requests through LiteLLM

**LiteLLM Dashboard Verification**:  
- Requests now showing as "Success" instead of "Failure"  
- Model names correctly formatted: `anthropic/claude-3-5-sonnet-20241022`  
- API calls completing successfully with proper model routing

---

## Migration Steps for xmarkdigest Repo

### 1. Update Database Migration

Add to `packages/database/prisma/migrations/20260122000149_refine_council_run/migration.sql`:

```sql
-- Add missing columns that were in schema but not in migration
ALTER TABLE "CouncilRun" 
ADD COLUMN IF NOT EXISTS "isGrounded" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS "personaIds" TEXT[] DEFAULT ARRAY[]::TEXT[];
```

### 2. Update Persona YAML Files

Update all Anthropic persona files in `packages/council/resources/personalities/`:

```yaml
# Change from:
model: anthropic/claude-3-5-sonnet

# To:
model: anthropic/claude-3-5-sonnet-20241022
```

Files to update:
- `anthropic_council_systems_strategist.yaml`
- `anthropic_council_operational_pragmatist.yaml`
- `anthropic_council_underlying_principles_analyst.yaml`
- `anthropic_council_adversarial_critic.yaml`

### 3. Update Seed Script

Update `packages/database/scripts/seed-council.ts` to use correct model names:

```typescript
// Ensure model names include date suffixes
model: model || 'anthropic/claude-3-5-sonnet-20241022',
```

### 4. Fix Persona Form Component

Update `apps/web/components/admin/council/persona-form.tsx`:

```tsx
<select
    // ... other props
    key={persona?.id || 'new'}  // Add this line
    defaultValue={persona?.model || 'anthropic/claude-3-sonnet-20240229'}
>
```

### 5. Regenerate Prisma Client

After updating migrations, regenerate Prisma client:

```bash
cd packages/database
pnpm prisma generate
```

---

## Prevention Recommendations

1. **Schema Validation**: Add a pre-deployment check to ensure Prisma schema matches database migrations
2. **Model Name Validation**: Create a validation function for model names to ensure LiteLLM compatibility
3. **Integration Tests**: Add tests that verify council functionality end-to-end, including model name resolution
4. **Documentation**: Document model naming conventions and LiteLLM compatibility requirements
5. **CI/CD Checks**: Add automated checks for:
   - Schema/migration consistency
   - Model name format validation
   - Form component state management

---

## Related Files

### Database
- `packages/database/prisma/schema.prisma` - Prisma schema definition
- `packages/database/prisma/migrations/20260122000149_refine_council_run/migration.sql` - Migration file (needs update)
- `packages/database/scripts/seed-council.ts` - Seed script (needs model name update)

### Council Engine
- `packages/council/src/engine.ts` - Council deliberation engine
- `packages/council/src/loader.ts` - Persona loader from database
- `packages/council/resources/personalities/*.yaml` - Persona definitions

### UI Components
- `apps/web/components/admin/council/persona-form.tsx` - Persona editing form
- `apps/web/app/admin/council/actions.ts` - Server actions for persona management
- `apps/web/app/api/council/deliberate/route.ts` - Council deliberation API endpoint

### Configuration
- `apps/web/.env.example` - Environment variable examples
- `packages/core/src/llm-client.ts` - LLM client configuration

---

## Notes

- All fixes have been applied to the production environment
- Database records have been updated directly (migrations should be updated for future deployments)
- Container was rebuilt to ensure Prisma client matches current schema
- Traefik was restarted to apply header changes (infrastructure repo)

---

**Contact**: For questions or clarifications about these fixes, please refer to this document or check the production deployment logs.
