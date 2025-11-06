# Authentication Research: Deep Dive Findings & Missing Considerations

**Date:** 2025-11-06
**Feature:** FEAT-013 Authentication & User Management
**Research Phase:** Complete

## Executive Summary

After comprehensive research into authentication options for EVI 360 RAG, I've identified **6 critical findings** you might not be aware of, **5 hypotheses** that need validation, and **7 open questions** requiring your input. The recommended path is a **phased approach**: start with OpenWebUI auth + shared PostgreSQL (1-hour setup), validate it meets 80% of needs, then enhance with custom features in Phases 2-3.

---

## What I Initially Missed (And Now Understand)

### 1. OpenWebUI Creates Its Own Database

**Initial Assumption:** OpenWebUI is just a UI that calls your API.

**Reality:** OpenWebUI is a **complete application** with its own:
- User management system (stores users, passwords, roles)
- Chat history storage (conversations, messages)
- JWT token generation (issues tokens on login)
- Database (SQLite by default, PostgreSQL via `DATABASE_URL`)

**Implication:** You have two options:
- **Option A**: Let OpenWebUI manage everything (users in its database)
- **Option B**: Share your PostgreSQL (OpenWebUI creates tables in `evi_rag` database)

**Recommendation:** Option B - allows querying users from Python if needed later

### 2. Your Backend Is Currently Unprotected

**Discovery:** Your FastAPI endpoints do NOT validate JWT tokens from OpenWebUI.

**Current Flow:**
```
User logs into OpenWebUI → Gets JWT token → Sends chat request
OpenWebUI adds: Authorization: Bearer <token>
Your FastAPI receives request → IGNORES token → Processes request
```

**Security Gap:** Anyone with `curl` can bypass OpenWebUI:
```bash
curl http://localhost:8058/v1/chat/completions \
  -d '{"message": "Show me all data"}'
  # ^ No authentication required!
```

**Fix Required (Phase 1, 2 hours):**
```python
# agent/auth.py (new file)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, WEBUI_SECRET_KEY, algorithms=["HS256"])
        return payload  # Contains: sub (user_id), email, role
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# Apply to all endpoints:
@app.post("/v1/chat/completions")
async def chat(request, user = Depends(verify_token)):
    user_id = user["sub"]
    # Now you know WHO is making the request
```

### 3. OpenWebUI 2FA Is Brand New (December 2024)

**Discovery:** TOTP 2FA support was only merged 1 month ago ([Discussion #16338](https://github.com/open-webui/open-webui/discussions/16338)).

**Implications:**
- May have bugs or missing features
- Sparse documentation
- Might require running `main` branch instead of stable release
- **MUST test thoroughly in Phase 1 experiment**

**Recommendation:** Don't assume 2FA "just works" - validate it before committing

### 4. Email Verification Not Built Into OpenWebUI

**Discovery:** OpenWebUI does NOT have native email verification for signups.

**What This Means:**
- Phase 2 must build custom email verification
- Cannot rely on OpenWebUI's auth alone
- Need to add: verification tokens, email sending, verified status check

**Implementation Required:**
```sql
-- Add to user table:
ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE user ADD COLUMN verification_token TEXT;
ALTER TABLE user ADD COLUMN verification_token_expires_at TIMESTAMP;
```

### 5. Invite-Only Registration Requires Custom Build

**Discovery:** Neither OpenWebUI nor standard FastAPI-users libraries provide invite-only registration out of the box.

**What You'll Need to Build (Phase 2):**
```sql
CREATE TABLE invitations (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    invite_token TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    invited_by UUID REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

```python
# Admin invites user:
POST /admin/invite
{
  "email": "user@example.com",
  "role": "user"
}

# System:
1. Creates invitation record
2. Generates unique token (UUID)
3. Sends email: "Click here to join: https://evi360.com/signup?token=abc123"

# User clicks link:
GET /signup?token=abc123
→ Shows signup form (pre-filled email, readonly)
→ User sets password
→ Creates account, marks invitation as used
```

### 6. GDPR Compliance Is More Complex Than "Delete User"

**Discovery:** GDPR Article 17 (Right to Erasure) requires:
- **30-day grace period** for account recovery
- **Data export** before deletion (portability)
- **Deletion from backups** (or exclusion when restoring)
- **Audit trail** of deletion (even though user is deleted)

**What You Must Build (Phase 3):**
```sql
-- Soft delete pattern:
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN deletion_requested_at TIMESTAMP;

-- User requests deletion:
UPDATE users
SET deletion_requested_at = NOW()
WHERE id = 'user-id';

-- Cron job runs daily:
DELETE FROM users
WHERE deletion_requested_at < NOW() - INTERVAL '30 days';

-- Before deletion, export data:
{
  "user": {...},
  "sessions": [...],
  "messages": [...],
  "audit_logs": [...]
}
```

---

## Missing Considerations (Now Documented in PRD)

### Security Considerations

1. **Rate Limiting**
   - Login attempts: Max 5 per IP per minute
   - Password reset: Max 3 per email per hour
   - API requests: Max 100 per user per minute

2. **Account Lockout**
   - After 5 failed login attempts → 15-minute lockout
   - Email notification: "Unusual activity detected"

3. **Session Management**
   - Max 5 concurrent sessions per user
   - "Logout all other devices" feature
   - Session list showing: device, browser, location, last active

4. **Audit Logging**
   - Events: login (success/fail), logout, password change, role change, permission denial
   - Stored in append-only table (tamper-proof)
   - 90-day minimum retention (compliance)

5. **Password Security**
   - Bcrypt hashing (cost factor 12)
   - zxcvbn strength scoring (reject weak passwords)
   - Minimum 12 characters recommended
   - No password reuse (store hash history)

### Compliance Considerations

1. **GDPR Requirements**
   - Right to erasure (account deletion with 30-day grace)
   - Right to data portability (export all user data)
   - Right to access (user can view all their data)
   - Data minimization (only collect necessary data)

2. **Data Retention**
   - Audit logs: Minimum 90 days, maximum 7 years
   - Deleted user data: Removed after 30-day grace period
   - Backup exclusion: Delete user data from backups when restoring

3. **Privacy by Design**
   - No tracking cookies without consent
   - Anonymize IP addresses in logs (last octet masked)
   - Encrypt sensitive data at rest (TOTP secrets, backup codes)

### Operational Considerations

1. **Email Infrastructure**
   - SMTP server or service (SendGrid, Mailgun, AWS SES)
   - SPF/DKIM/DMARC records for deliverability
   - Templates: invitation, password reset, email verification, security alerts
   - Unsubscribe mechanism (even for transactional emails)

2. **Monitoring & Alerting**
   - Failed login spike (potential brute force)
   - Mass password reset requests (potential breach)
   - Account lockouts (user frustration indicator)
   - API error rates (authentication issues)

3. **Backup & Recovery**
   - Database backups include authentication tables
   - Backup encryption (passwords already hashed, but backup codes and TOTP secrets are sensitive)
   - Recovery testing (can we restore auth system after failure?)

4. **User Support**
   - Password reset when user loses access to 2FA device
   - Backup code regeneration (if user loses codes)
   - Account recovery (if user is locked out)
   - Admin override capability (with audit logging)

---

## Phased Approach: Why It Makes Sense

### Phase 1: OpenWebUI Auth (Week 1) - Validation Phase

**Goal:** Prove that authentication works and meets 80% of requirements

**What You Build:**
1. Enable `WEBUI_AUTH=true` in docker-compose
2. Configure `DATABASE_URL` to share PostgreSQL
3. Add FastAPI JWT validation middleware (2 hours)
4. Test with 3-5 users for 1 week

**What You Validate:**
- ✅ Hypothesis 1: 2-role UI is acceptable
- ✅ Hypothesis 4: Backend enforcement prevents bypasses
- ✅ Hypothesis 5: Shared PostgreSQL works without conflicts

**Deliverables:**
- Working authentication (1 hour setup)
- Secured FastAPI backend (2 hours)
- User feedback on UX (1 week testing)
- Go/no-go decision on Phase 2

**If Successful:** Proceed to Phase 2 (add advanced features to hybrid system)
**If Not:** Skip to custom FastAPI JWT implementation from scratch

### Phase 2: Advanced Features (Weeks 2-4) - Enhancement Phase

**Prerequisites:** Phase 1 validated that hybrid approach is viable

**What You Build:**
1. Admin invite system (email invitations)
2. Email verification for new signups
3. Password reset flow
4. 2FA/TOTP integration (if OpenWebUI 2FA works)
5. Backend role enforcement (4 roles)
6. Session management (view/revoke sessions)

**What You Validate:**
- ✅ Hypothesis 2: Invite workflow is efficient for admins
- ✅ Hypothesis 3: Users adopt 2FA without resistance

**Deliverables:**
- Invitation system (~2 days)
- Email verification (~1 day)
- Password reset (~1 day)
- 2FA integration (~2 days)
- Role enforcement (~2 days)
- Session management (~1 day)

**Total:** ~2 weeks

### Phase 3: Compliance & Polish (Weeks 5-6) - Production-Ready

**What You Build:**
1. GDPR-compliant account deletion (30-day grace)
2. Audit logging system (tamper-proof, 90-day retention)
3. Rate limiting on auth endpoints
4. Account lockout after failed attempts
5. Security event notifications (password change, new device)

**Deliverables:**
- Account deletion flow (~3 days)
- Audit logging system (~2 days)
- Rate limiting & lockout (~1 day)
- Email notifications (~1 day)

**Total:** ~1 week

---

## Open Questions Requiring Your Input

### Critical Questions (Block Phase 1)

**Q1: Role Permission Matrix**
I need to know what each role can/cannot do:

| Action | Admin | Superuser | User | Readonly |
|--------|-------|-----------|------|----------|
| Chat with agent | ? | ? | ? | ? |
| Search guidelines | ? | ? | ? | ? |
| Search products | ? | ? | ? | ? |
| View own chat history | ? | ? | ? | ? |
| View others' chats | ? | ? | ? | ? |
| Manage users | ? | ? | ? | ? |
| View audit logs | ? | ? | ? | ? |
| Configure system | ? | ? | ? | ? |

**Q2: Email Service**
Which email service should I integrate?
- A) SendGrid (100 emails/day free, easy setup)
- B) AWS SES ($0.10/1000 emails, requires AWS account)
- C) Mailgun (25,000 emails/month free)
- D) Self-hosted SMTP (requires email server)

**My Recommendation:** Start with SendGrid for Phase 1 (easiest), migrate to AWS SES if you already use AWS

### Important Questions (Can defer to Phase 2)

**Q3: 2FA Enforcement**
- A) Mandatory for all users
- B) Mandatory for admins/superusers only
- C) Optional for everyone
- D) Configurable per-user

**My Recommendation:** Option B (mandatory for elevated privileges, optional for regular users)

**Q4: Password Policy**
- A) Minimum 8 characters, no other rules
- B) 12 characters, uppercase + lowercase + number + special
- C) 16 characters passphrase-style
- D) zxcvbn-based strength scoring

**My Recommendation:** Option D (strength scoring, reject weak passwords)

**Q5: Account Lockout**
After how many failed login attempts should we lock account?
- A) 3 attempts → 30 minutes
- B) 5 attempts → 15 minutes (recommended)
- C) 10 attempts → 1 hour

**Q6: Concurrent Sessions**
Maximum sessions per user?
- A) Unlimited
- B) 5 sessions (recommended)
- C) 3 sessions
- D) 1 session only

**Q7: EU Server Timeline**
When do you plan to deploy to EU server?
- This affects whether we optimize for local dev or production from day 1

---

## Next Steps

### Immediate Actions for You

1. **Review PRD**: Read `docs/features/FEAT-013_authentication-and-user-management/prd.md`
2. **Answer Q1 & Q2** (critical for Phase 1)
3. **Approve or provide feedback** on phased approach
4. **Decide**: Run Phase 1 experiment this week, or skip to custom JWT?

### If You Approve Phase 1 Experiment

I will:
1. Create docker-compose configuration updates
2. Write FastAPI JWT validation middleware
3. Create test script for validation
4. Document step-by-step Phase 1 setup instructions
5. Create user test feedback form

**Time to Phase 1 deployment:** ~4 hours of implementation, 1 week of user testing

### If You Want to Skip to Custom JWT

I will:
1. Create full database schema (users, invitations, audit_logs, etc.)
2. Implement FastAPI JWT auth from scratch
3. Build all Phase 2 features immediately
4. Estimated time: 2-3 weeks before you can test

---

## Summary of Trade-Offs

| Aspect | OpenWebUI Auth (Phase 1) | Custom FastAPI JWT |
|--------|--------------------------|---------------------|
| Time to working auth | 1 hour | 1-2 weeks |
| Roles in UI | 2 only (admin, user) | 4 custom roles |
| 2FA support | Built-in (if it works) | DIY (2-3 days) |
| Email verification | DIY (Phase 2) | DIY (1 day) |
| Invite workflow | DIY (Phase 2) | DIY (2 days) |
| Control over schema | Limited | Full control |
| Maintenance burden | OpenWebUI maintains | You maintain |
| Migration risk | Can always switch later | Committed to custom |
| Database | Shared PostgreSQL | Your PostgreSQL |

**My Recommendation:** Start with Phase 1, validate it works, then decide if you need to switch to custom JWT or continue enhancing the hybrid approach.

---

**Status:** Awaiting your decisions on critical questions before proceeding to implementation planning.
