# Twitter OAuth Infinite Loop - Hypothesis Analysis

**Date**: January 28, 2026  
**Issue**: User gets stuck in infinite loop on Twitter OAuth authorization page  
**URL Pattern**: `https://twitter.com/i/oauth2/authorize?...redirect_uri=https://accordant.eu/api/auth/callback/twitter...`  
**Context**: **EXISTING USER** trying to link Twitter account via Settings → Connections tab (NOT sign-up)

## Critical Context Update

⚠️ **IMPORTANT**: This is NOT a sign-up flow. The user is:
1. Already logged in with email/password
2. Navigating to `/settings?tab=connections`
3. Clicking "Connect" button for Twitter
4. Getting stuck in OAuth loop

This changes the analysis significantly - NextAuth needs to **link** the OAuth account to the existing user, not create a new user.

## Top 5 Hypotheses (Ranked by Likelihood)

### Hypothesis 1: Missing `signIn` Callback for Account Linking ⭐⭐⭐⭐⭐
**Likelihood**: **VERY HIGH** (95%)

**Evidence**:
- User is already authenticated (email/password account exists)
- Clicking "Connect Twitter" calls `signIn('twitter', { callbackUrl: '/settings/connections' })`
- NextAuth by default creates a NEW user when OAuth provider doesn't match existing account
- No `signIn` callback exists to handle linking OAuth account to existing user
- NextAuth throws `OAuthAccountNotLinked` error, redirects to error page (`/`)
- Error page redirects back to login, creating infinite loop

**Root Cause Analysis**:
```typescript
// lib/auth.ts - NO signIn callback exists!
callbacks: {
    async jwt({ token, user, trigger: _trigger }) {
        // Only handles JWT token creation
    },
    async session({ session, token }) {
        // Only handles session creation
    },
    // ❌ MISSING: async signIn({ user, account, profile }) { ... }
},
```

**NextAuth Behavior**:
- When an authenticated user calls `signIn('twitter')`, NextAuth:
  1. Completes OAuth flow with Twitter
  2. Gets Twitter account info
  3. Checks if account exists → No (first time linking)
  4. Checks if user with Twitter email exists → Maybe (if Twitter email matches)
  5. **If email matches but account not linked**: Throws `OAuthAccountNotLinked` error
  6. Redirects to error page (`/`)
  7. Error page redirects unauthenticated users to `/login`
  8. **Loop continues**

**How to Verify**:
```bash
# Check for OAuthAccountNotLinked errors
docker logs ai-stack_accordant_web --tail 200 | grep -i "OAuthAccountNotLinked\|account.*not.*linked\|error"

# Check if user exists with email that might match Twitter
docker exec ai-stack_db psql -U accordant -d accordant -c "SELECT id, email, name FROM \"User\" WHERE email IS NOT NULL;"
```

**Fix**:
Add `signIn` callback to handle account linking:

```typescript
callbacks: {
    async signIn({ user, account, profile }) {
        // If user is already authenticated (session exists), link account
        if (account && account.provider === 'twitter') {
            // Get current session user ID
            const session = await getServerSession(authOptions);
            if (session?.user?.id) {
                // Link Twitter account to existing user
                await prisma.account.create({
                    data: {
                        userId: session.user.id,
                        type: account.type,
                        provider: account.provider,
                        providerAccountId: account.providerAccountId,
                        refresh_token: account.refresh_token,
                        access_token: account.access_token,
                        expires_at: account.expires_at,
                        token_type: account.token_type,
                        scope: account.scope,
                    },
                });
                return true; // Allow sign-in
            }
        }
        return true; // Default: allow sign-in
    },
    // ... existing callbacks
}
```

**Alternative Fix** (Better approach):
Use NextAuth's built-in account linking by checking if user is already signed in:

```typescript
callbacks: {
    async signIn({ user, account, profile, email }) {
        // If account already exists, allow sign-in (account linking)
        if (account) {
            const existingAccount = await prisma.account.findUnique({
                where: {
                    provider_providerAccountId: {
                        provider: account.provider,
                        providerAccountId: account.providerAccountId,
                    },
                },
            });
            
            if (existingAccount) {
                return true; // Account already linked
            }
            
            // If user is already authenticated, link the account
            // This requires checking the session, which is tricky in signIn callback
            // Better approach: Use linkAccount event or handle in a custom route
        }
        return true;
    },
}
```

**Best Fix** (Recommended):
Handle account linking in a custom API route or use NextAuth's `linkAccount` event:

```typescript
events: {
    async linkAccount({ user, account, profile }) {
        logger.info({ userId: user.id, provider: account.provider }, '[OAuth] Account linked');
        // Account is automatically linked by PrismaAdapter
        // This event fires after successful linking
    },
}
```

But the real issue is that `signIn('twitter')` from an authenticated user doesn't automatically link - it tries to sign in as a new user. Need to use a different approach for account linking.

---

### Hypothesis 2: Organization Provisioning Failure in `createUser` Event ⭐⭐⭐⭐
**Likelihood**: **HIGH** (70%) - Still relevant if NextAuth creates new user instead of linking

**Evidence**:
- The `createUser` event handler in `lib/auth.ts` (lines 115-154) attempts to create an Organization
- If this fails, NextAuth may not complete the sign-in process
- No Twitter accounts exist in database (`SELECT COUNT(*) FROM Account WHERE provider = 'twitter'` returns 0)
- Error page is set to `/` which likely redirects back to login

**Root Cause Analysis**:
```typescript
// lib/auth.ts lines 137-149
const newOrg = await prisma.organization.create({
    data: {
        name: `${name}'s Workspace`,
        slug,
        type: 'PERSONAL',
        members: {
            create: {
                userId: user.id,
                role: 'OWNER',
            },
        },
    },
});
```

**Potential Failure Points**:
1. **Slug collision**: If slug generation creates a duplicate, `findUnique` might miss it due to race condition
2. **Database constraint violation**: Organization creation might fail silently
3. **Transaction rollback**: If organization creation fails, user creation might rollback
4. **Error swallowed**: Error is caught but doesn't prevent NextAuth from continuing with incomplete state

**How to Verify**:
```bash
# Check for any users created during OAuth attempts
docker exec ai-stack_db psql -U accordant -d accordant -c "SELECT id, email, name, createdAt FROM \"User\" ORDER BY createdAt DESC LIMIT 5;"

# Check for partial organizations
docker exec ai-stack_db psql -U accordant -d accordant -c "SELECT id, name, slug FROM \"Organization\" ORDER BY createdAt DESC LIMIT 5;"

# Check application logs during OAuth attempt
docker logs ai-stack_accordant_web --tail 100 | grep -i "createUser\|organization\|error"
```

**Fix**:
- Add better error handling in `createUser` event
- Make organization creation non-blocking (don't fail OAuth if org creation fails)
- Add retry logic for slug collisions
- Log errors more explicitly

---

### Hypothesis 3: Error Page Redirecting Back to Auth ⭐⭐⭐⭐
**Likelihood**: **HIGH** (80%) - More likely now that we know it's account linking

**Evidence**:
- NextAuth error page is configured as `error: '/'` (line 158 in auth.ts)
- If OAuth callback fails, NextAuth redirects to `/`
- Root page (`/`) might redirect unauthenticated users back to `/login`
- Login page has Twitter button that triggers OAuth again

**Root Cause Analysis**:
```typescript
// lib/auth.ts line 158
pages: {
    signIn: '/login',
    error: '/',  // ← This redirects to root
},
```

**Flow**:
1. User authorizes on Twitter
2. Callback fails (for any reason)
3. NextAuth redirects to `/` (error page)
4. Root page checks auth, finds none
5. Redirects to `/login`
6. User sees login page, clicks Twitter again
7. **Loop continues**

**How to Verify**:
- Check if root page (`/`) has auth redirect logic
- Monitor browser network tab during OAuth attempt
- Check for redirect chain: `/api/auth/callback/twitter` → `/` → `/login` → Twitter OAuth

**Fix**:
- Create dedicated error page: `error: '/auth/error'`
- Show specific error message instead of redirecting
- Add error query parameter handling: `?error=oauth_failed`

---

### Hypothesis 4: Session Lost During OAuth Flow ⭐⭐⭐
**Likelihood**: **MEDIUM** (60%) - Session might be lost when redirecting to Twitter

**Evidence**:
- Session strategy is JWT (line 13: `strategy: 'jwt'`)
- JWT callback (lines 74-92) might fail if user lookup fails
- If session creation fails, NextAuth redirects to error page
- No sessions exist for OAuth users (inferred from no accounts)

**Root Cause Analysis**:
```typescript
// lib/auth.ts lines 74-92
async jwt({ token, user, trigger: _trigger }) {
    if (user) {
        token.userId = user.id;
        token.role = user.role;
        token.emailVerified = user.emailVerified;
    } else if (token.userId) {
        // This might fail if user was deleted or doesn't exist
        const freshUser = await prisma.user.findUnique({
            where: { id: token.userId as string },
            select: { role: true, emailVerified: true },
        });
        // ...
    }
    return token;
}
```

**Potential Failure Points**:
1. User created but immediately deleted due to error
2. JWT token created but user lookup fails
3. Role/emailVerified fields missing causing token creation to fail
4. Database transaction rollback after token creation

**How to Verify**:
```bash
# Check for any sessions
docker exec ai-stack_db psql -U accordant -d accordant -c "SELECT COUNT(*) FROM \"Session\";"

# Check for users without accounts (orphaned users)
docker exec ai-stack_db psql -U accordant -d accordant -c "SELECT u.id, u.email FROM \"User\" u LEFT JOIN \"Account\" a ON a.\"userId\" = u.id WHERE a.id IS NULL;"
```

**Fix**:
- Add error handling in JWT callback
- Ensure user exists before creating token
- Add fallback values for missing fields

---

### Hypothesis 5: PKCE Code Challenge Mismatch ⭐⭐
**Likelihood**: **LOW-MEDIUM** (40%)

**Evidence**:
- OAuth URL includes `code_challenge` and `code_challenge_method=S256`
- NextAuth handles PKCE automatically, but configuration might be incorrect
- If code verifier doesn't match challenge, Twitter rejects the callback
- NextAuth might retry authorization automatically

**Root Cause Analysis**:
- PKCE (Proof Key for Code Exchange) requires:
  1. `code_challenge` in authorization URL (present ✓)
  2. `code_verifier` in token exchange (handled by NextAuth)
  3. Challenge must be SHA256 hash of verifier

**Potential Failure Points**:
1. NextAuth not storing code_verifier correctly
2. Code verifier lost between redirects
3. Session storage issue preventing verifier retrieval
4. Multiple OAuth attempts overwriting verifier

**How to Verify**:
- Check NextAuth logs for PKCE-related errors
- Monitor callback URL for error parameters
- Check if `code` parameter is present in callback

**Fix**:
- Verify NextAuth PKCE configuration
- Check session storage configuration
- Ensure cookies are set correctly (SameSite, Secure flags)

---

### Hypothesis 6: Callback URL Mismatch or CORS Issue ⭐⭐
**Likelihood**: **LOW** (25%)

**Evidence**:
- Callback URL: `https://accordant.eu/api/auth/callback/twitter`
- Twitter OAuth app must have exact callback URL registered
- CORS or security headers might block the callback

**Root Cause Analysis**:
- Twitter requires exact match of redirect_uri
- If callback URL doesn't match registered URL, Twitter rejects
- NextAuth might retry with same parameters

**Potential Failure Points**:
1. Callback URL not registered in Twitter Developer Portal
2. URL encoding issues (`%2F` vs `/`)
3. Traefik/proxy rewriting URLs
4. HTTPS vs HTTP mismatch

**How to Verify**:
```bash
# Check Twitter app callback URLs
# (Requires access to Twitter Developer Portal)

# Check Traefik routing
docker logs ai-stack_traefik --tail 50 | grep "callback/twitter"

# Test callback endpoint directly
curl -I https://accordant.eu/api/auth/callback/twitter
```

**Fix**:
- Verify callback URL in Twitter Developer Portal matches exactly
- Check Traefik labels for correct routing
- Ensure HTTPS is properly configured

---

## Recommended Investigation Steps

### Step 1: Check Application Logs During OAuth Attempt
```bash
# Clear logs, then attempt OAuth, then check
docker logs ai-stack_accordant_web --tail 200 | grep -E "createUser|organization|error|twitter|oauth" -i
```

### Step 2: Check Database State
```bash
# Check for partial user creation
docker exec ai-stack_db psql -U accordant -d accordant -c "
SELECT 
    u.id, 
    u.email, 
    u.name,
    u.createdAt,
    (SELECT COUNT(*) FROM \"Account\" WHERE \"userId\" = u.id) as account_count,
    (SELECT COUNT(*) FROM \"Membership\" WHERE \"userId\" = u.id) as membership_count
FROM \"User\" u 
ORDER BY u.createdAt DESC 
LIMIT 10;"
```

### Step 3: Test Error Page Behavior
- Manually navigate to `/api/auth/callback/twitter?error=test`
- Check what happens
- Verify redirect chain

### Step 4: Add Debug Logging
Add logging to `createUser` event:
```typescript
events: {
    async createUser({ user }) {
        logger.info({ userId: user.id, email: user.email }, '[OAuth] createUser event started');
        try {
            // ... existing code ...
            logger.info({ userId: user.id, orgId: newOrg.id }, '[OAuth] createUser completed successfully');
        } catch (err) {
            logger.error({ userId: user.id, error: err }, '[OAuth] createUser FAILED');
            // Don't throw - let NextAuth complete
        }
    },
}
```

---

## Most Likely Root Cause

**Hypothesis 1** (Missing `signIn` Callback for Account Linking) is the most likely cause because:

1. ✅ User is already authenticated (not signing up)
2. ✅ NextAuth doesn't automatically link OAuth accounts to existing users
3. ✅ No `signIn` callback exists to handle account linking
4. ✅ NextAuth likely throws `OAuthAccountNotLinked` error
5. ✅ Error page (`/`) redirects back to login, creating loop
6. ✅ This is a common NextAuth issue for account linking

**Previous Hypothesis 1** (Organization Provisioning Failure) is still relevant if NextAuth creates a new user instead of linking, because:

1. ✅ No Twitter accounts exist (OAuth never completes)
2. ✅ `createUser` event has complex logic that could fail
3. ✅ Error handling swallows errors but doesn't prevent issues
4. ✅ Organization creation is synchronous and blocking
5. ✅ Slug collision could cause silent failures

## Recommended Immediate Fix

### Primary Fix: Add Account Linking Support

The issue is that `signIn('twitter')` from an authenticated user doesn't link accounts - it tries to create a new user. NextAuth needs explicit account linking.

**Option 1: Use NextAuth's Account Linking Pattern**

Create a custom API route for account linking:

```typescript
// app/api/auth/link/[provider]/route.ts
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { prisma } from '@repo/database';
import { NextResponse } from 'next/server';

export async function GET(req: Request, { params }: { params: { provider: string } }) {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
        return NextResponse.redirect('/login');
    }
    
    // Redirect to OAuth with special parameter
    const callbackUrl = `/api/auth/link/callback/${params.provider}`;
    // Use NextAuth's signIn but handle linking in callback
}
```

**Option 2: Modify signIn Callback (Simpler)**

Add `signIn` callback to handle linking:

```typescript
// lib/auth.ts
callbacks: {
    async signIn({ user, account, profile, email }) {
        // If account exists, allow (already linked)
        if (account) {
            const existing = await prisma.account.findUnique({
                where: {
                    provider_providerAccountId: {
                        provider: account.provider,
                        providerAccountId: account.providerAccountId,
                    },
                },
            });
            if (existing) return true;
        }
        
        // Check if user is already authenticated (session exists)
        // This is tricky - signIn callback doesn't have direct session access
        // Better: Handle in linkAccount event or custom route
        
        return true; // Allow sign-in, handle linking elsewhere
    },
    // ... existing callbacks
},
events: {
    async linkAccount({ user, account, profile }) {
        logger.info({ userId: user.id, provider: account.provider }, '[OAuth] Account linked successfully');
    },
    // ... existing createUser event
}
```

**Option 3: Use NextAuth's Built-in Account Linking (Best)**

NextAuth with PrismaAdapter should handle account linking automatically IF:
1. The OAuth provider returns an email
2. That email matches an existing user's email
3. But this requires the `signIn` callback to return `true`

The real issue: When clicking "Connect Twitter" from settings, NextAuth doesn't know to link to the current user. It treats it as a new sign-in.

**Recommended Solution**: Use a custom account linking flow:

```typescript
// In connection-list.tsx, instead of signIn('twitter'):
const handleConnectTwitter = async () => {
    setIsLoading(true);
    // Store current user ID in session/cookie
    // Redirect to custom OAuth flow that links account
    window.location.href = `/api/auth/link/twitter?userId=${session.user.id}`;
};
```

### Secondary Fix: Make organization creation non-blocking (if new users are created):

```typescript
events: {
    async createUser({ user }) {
        // Run provisioning in background, don't block OAuth
        setImmediate(async () => {
            try {
                // ... existing provisioning logic ...
            } catch (err) {
                logger.error({ userId: user.id, error: err }, '[OAuth] Provisioning failed (non-blocking)');
                // Log but don't throw - OAuth should succeed even if provisioning fails
            }
        });
    },
}
```

Or use a queue/job system for provisioning to avoid blocking the OAuth flow.

---

## Additional Notes

- The warning `[next-auth][warn][TWITTER_OAUTH_2_BETA]` is expected and not related to the loop
- The callback URL format looks correct
- PKCE implementation appears standard
- The issue is likely in the post-OAuth user provisioning logic

---

**Last Updated**: January 28, 2026
