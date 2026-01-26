# Security Incident - Exposed Secrets

## Date
2026-01-26

## Issue
The file `SETUP_COMPLETE.md` containing sensitive credentials was committed to git and pushed to GitHub. This file contained:
- Database password
- NextAuth secret
- Encryption key

## Actions Taken

1. ✅ Added `SETUP_COMPLETE.md` to `.gitignore`
2. ✅ Removed file from git tracking
3. ✅ Removed file from entire git history using `git filter-branch`
4. ✅ Cleaned up git references and garbage collected

## Required Actions

### ⚠️ CRITICAL: Rotate All Exposed Secrets

Since the secrets were already pushed to GitHub, they are potentially exposed. You **MUST** rotate all of them:

1. **Database Password** (`ACCORDANT_DB_PASSWORD`)
   - Generate new password: `openssl rand -base64 32`
   - Update in `.env` file
   - Update PostgreSQL user password:
     ```sql
     ALTER USER accordant WITH PASSWORD 'new_password_here';
     ```

2. **NextAuth Secret** (`NEXTAUTH_SECRET`)
   - Generate new secret: `openssl rand -base64 32`
   - Update in `.env` file
   - **Note**: This will invalidate all existing user sessions

3. **Encryption Key** (`ENCRYPTION_KEY`)
   - Generate new key: `openssl rand -hex 32`
   - Update in `.env` file
   - **Note**: Any encrypted data using the old key will need to be re-encrypted or migrated

### Force Push to Remote

After rotating secrets, you need to force push to update the remote repository:

```bash
cd /root/apps/accordant
git push --force-with-lease origin main
```

**Warning**: Force pushing rewrites history. If others are working on this repository, coordinate with them first. They will need to:
```bash
git fetch origin
git reset --hard origin/main
```

### Verify Removal

After force pushing, verify the file is no longer accessible on GitHub:
- Check the repository on GitHub
- Confirm `SETUP_COMPLETE.md` is not visible in any commit history
- If using GitHub's secret scanning, check for any alerts

## Prevention

Going forward:
- ✅ `SETUP_COMPLETE.md` is now in `.gitignore`
- ✅ Never commit files containing passwords or secrets
- ✅ Use `.env.example` files with placeholder values for documentation
- ✅ Review files before committing with `git status` and `git diff`

## Files Modified

- `.gitignore` - Added `SETUP_COMPLETE.md` to ignore list
- Git history - Removed `SETUP_COMPLETE.md` from all commits
