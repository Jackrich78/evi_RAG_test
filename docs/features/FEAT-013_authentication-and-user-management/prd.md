# Product Requirements Document: Authentication & User Management

**Feature ID:** FEAT-013
**Status:** Exploring
**Created:** 2025-11-06
**Last Updated:** 2025-11-06

## Problem Statement

The EVI 360 RAG system currently has no authentication, allowing anyone with network access to use the system. For deployment to EVI 360 workplace safety specialists (10-50 users), we need secure multi-user access with role-based permissions, user management, and compliance with security best practices. The system must support admin-managed user provisioning, enforce role-based access control at the backend level, and provide features like 2FA, password reset, and email verification for a production-ready deployment.

## Goals & Success Criteria

### Primary Goals
- **Goal 1**: Implement secure authentication that prevents unauthorized access to the EVI 360 RAG system
- **Goal 2**: Enable admin-managed user provisioning with email invitations (no self-registration)
- **Goal 3**: Support 4 role types (admin, superuser, user, readonly) with backend enforcement
- **Goal 4**: Provide enterprise security features: 2FA, password reset, email verification
- **Goal 5**: Maintain local-first architecture (trajectory: EU server deployment with HTTPS)

### Success Metrics
- Zero unauthorized access attempts successful
- All users can login with 2FA within 2 minutes
- Password reset flow completes in < 5 minutes
- Role permissions correctly enforced (0 permission bypass incidents)
- Admin can provision new user in < 3 minutes

## User Stories

### Story 1: Admin Invites New User
**As an** EVI 360 system administrator
**I want** to invite new users via email invitation
**So that** only authorized EVI 360 specialists can access the system

**Acceptance Criteria:**
- [ ] Admin can enter user email and assign initial role (superuser, user, or readonly)
- [ ] System sends invitation email with unique signup link (24-hour expiry)
- [ ] User clicks link, sets password (with strength requirements), and completes account setup
- [ ] Invitation link becomes invalid after use or expiry
- [ ] Admin can see list of pending invitations and resend/revoke them

### Story 2: User Logs In with 2FA
**As an** EVI 360 workplace safety specialist
**I want** to log in securely with two-factor authentication
**So that** my account cannot be compromised even if my password is stolen

**Acceptance Criteria:**
- [ ] User enters email and password
- [ ] System prompts for TOTP code (Google Authenticator / Authy)
- [ ] User scans QR code on first login to set up 2FA
- [ ] System provides backup codes (10 single-use codes) during 2FA setup
- [ ] Login succeeds only with valid password + valid TOTP code
- [ ] Failed 2FA attempts are logged for security auditing

### Story 3: User Resets Forgotten Password
**As an** EVI 360 specialist who forgot my password
**I want** to reset it via email link
**So that** I can regain access without admin intervention

**Acceptance Criteria:**
- [ ] User clicks "Forgot Password" on login page
- [ ] User enters email address
- [ ] System sends password reset email with unique link (1-hour expiry)
- [ ] User clicks link, enters new password (must meet strength requirements)
- [ ] System invalidates all existing sessions for that user
- [ ] User can log in with new password
- [ ] Password reset attempts are rate-limited (max 3 per hour per email)

### Story 4: Backend Enforces Role Permissions
**As a** developer integrating authentication
**I want** the FastAPI backend to enforce role-based permissions
**So that** users can only access features appropriate to their role

**Acceptance Criteria:**
- [ ] FastAPI validates JWT token on every request
- [ ] Endpoint decorators check user role against required permissions
- [ ] Readonly users can search guidelines/products but cannot create sessions
- [ ] Regular users can chat and search (full OpenWebUI access)
- [ ] Superusers can access advanced features (TBD: analytics, bulk operations)
- [ ] Admins can manage users, view audit logs, configure system settings
- [ ] Permission violations return 403 Forbidden with clear error message

### Story 5: Admin Views Audit Logs
**As an** admin
**I want** to see audit logs of user authentication and access events
**So that** I can investigate security incidents and ensure compliance

**Acceptance Criteria:**
- [ ] System logs: login attempts (success/fail), logout, password reset, role changes, invitation sent
- [ ] Admin can filter logs by: user, event type, date range, success/failure
- [ ] Logs include: timestamp, user_id, event type, IP address, user agent, outcome
- [ ] Logs are tamper-proof (append-only table with integrity checks)
- [ ] Logs retained for minimum 90 days (GDPR compliance)

### Story 6: User Deletes Their Account (GDPR Compliance)
**As an** EVI 360 specialist
**I want** to request deletion of my account and personal data
**So that** my privacy rights under GDPR are respected

**Acceptance Criteria:**
- [ ] User can initiate account deletion from settings page
- [ ] System requires password confirmation for deletion request
- [ ] System queues deletion for 30-day grace period (allows account recovery)
- [ ] User receives email confirming deletion request with cancellation link
- [ ] After 30 days, system permanently deletes: user account, sessions, messages, audit logs (excluding deletion event)
- [ ] Guidelines and products (shared resources) are NOT deleted
- [ ] Admin can export user data before deletion (GDPR data portability)

### Story 7: Concurrent Session Management
**As an** EVI 360 specialist
**I want** to know which devices I'm logged in on
**So that** I can ensure my account security

**Acceptance Criteria:**
- [ ] User can view list of active sessions (device type, browser, location, last active time)
- [ ] User can revoke individual sessions or "logout all other devices"
- [ ] System enforces maximum 5 concurrent sessions per user
- [ ] Oldest session is automatically invalidated when limit exceeded
- [ ] Session revocation takes effect immediately (next request fails)

## Scope & Non-Goals

### In Scope
**Phase 1: Foundation (Week 1)**
- OpenWebUI authentication enabled (WEBUI_AUTH=true)
- Shared PostgreSQL database (not SQLite)
- Admin/User roles in OpenWebUI UI
- FastAPI JWT token validation middleware
- Basic session management

**Phase 2: Advanced Features (Weeks 2-4)**
- Admin invite-only user provisioning (email invitations)
- Email verification for new signups
- Password reset flow
- 2FA/TOTP support
- Backend role enforcement (4 roles: admin, superuser, user, readonly)
- Audit logging system
- Session management (view active sessions, revoke sessions)

**Phase 3: Compliance & Polish (Weeks 5-6)**
- GDPR-compliant account deletion
- Rate limiting on auth endpoints
- Account lockout after failed login attempts
- Email notifications for security events (password change, new device login)
- Admin user management UI improvements

### Out of Scope (For This Version)
- **Social login (Google, Microsoft, GitHub)** - Reason: Internal tool, email-based auth sufficient
- **Single Sign-On (SSO) / SAML** - Reason: Not required for initial 10-50 users, can add later
- **Magic links / passwordless auth** - Reason: Users prefer traditional password + 2FA
- **Custom OpenWebUI UI modifications** - Reason: Use OpenWebUI as-is, enforce roles in backend
- **Mobile app authentication** - Reason: Web-only for foreseeable future
- **Integration with Active Directory / LDAP** - Reason: Not required for EVI 360 deployment

## Constraints & Assumptions

### Technical Constraints
- **TC-1: OpenWebUI Limited to 2 Roles in UI** - OpenWebUI natively supports only admin/user roles. Our 4 roles (admin, superuser, user, readonly) must be stored in our PostgreSQL `users` table and enforced in FastAPI backend, not in OpenWebUI UI.
- **TC-2: Shared PostgreSQL Database** - OpenWebUI will create its own tables (`user`, `chat`, `message`, etc.) in our `evi_rag` PostgreSQL database. We need to avoid table name conflicts.
- **TC-3: JWT Token Compatibility** - Must use same `WEBUI_SECRET_KEY` for OpenWebUI and FastAPI to validate tokens.
- **TC-4: Local Development → EU Production Trajectory** - Currently developing locally; eventual deployment to EU-based server with HTTPS/SSL.
- **TC-5: Email Service Required** - Need SMTP server or email service (e.g., SendGrid, Mailgun, AWS SES) for invitation/reset/verification emails.

### Business Constraints
- **BC-1: Timeline**: Phase 1 must complete in 1 week (rapid prototype), Phases 2-3 within 6 weeks total
- **BC-2: User Base**: Initial 10 users, scale to 50 users within 6 months
- **BC-3: Admin-Managed**: Only admins can invite users (no self-registration)
- **BC-4: Compliance**: Must support GDPR requirements (account deletion, data export)

### Assumptions
- **A-1: OpenWebUI Frontend Only** - Will use OpenWebUI as primary/only frontend for foreseeable future (no custom React app planned)
- **A-2: HTTPS in Production** - EU server deployment will have SSL/HTTPS configured
- **A-3: PostgreSQL for User Data** - Don't need to query users from Python frequently, but prefer all data in one database
- **A-4: Email Delivery Reliable** - Users have access to email and can receive invitation/reset emails promptly
- **A-5: Users Are Tech-Savvy Enough** - EVI 360 specialists can use Google Authenticator app for 2FA
- **A-6: Dutch Language UI** - OpenWebUI already configured for Dutch (DEFAULT_LOCALE=nl), auth flows should support Dutch text

## Trade-Off Decisions

### Decision 1: OpenWebUI Auth (Phase 1) → Custom FastAPI JWT (Phase 2)
**Options Considered:**
- A) OpenWebUI auth only
- B) Custom FastAPI JWT from day 1
- C) Authentik (open-source IAM)
- D) Supabase Auth (managed service)

**Decision:** Start with Option A (OpenWebUI auth), migrate to hybrid approach in Phase 2

**Rationale:**
- **Speed**: OpenWebUI auth works in 1 hour vs. 1-2 weeks for custom JWT
- **Validation**: Can test if 2-role system is acceptable before investing in custom solution
- **Flexibility**: Can always add custom JWT layer later
- **Risk Mitigation**: Proves out authentication flow before committing to architecture

**Trade-offs Accepted:**
- ⚠️ Limited to 2 roles in UI initially (enforced in backend code)
- ⚠️ OpenWebUI manages users (less control over user schema)
- ⚠️ Potential migration cost if we need full custom JWT later

### Decision 2: Shared PostgreSQL Instead of Separate OpenWebUI SQLite
**Options Considered:**
- A) Let OpenWebUI use SQLite (default)
- B) Configure OpenWebUI to use shared PostgreSQL

**Decision:** Option B (shared PostgreSQL)

**Rationale:**
- Single backup point (one database, not two)
- Can query users from Python if needed later
- Better for production deployment (PostgreSQL scales better than SQLite)
- Aligns with "local-first, then EU server" trajectory

**Trade-offs Accepted:**
- ⚠️ OpenWebUI creates ~20 tables in our database (potential namespace pollution)
- ⚠️ Must coordinate schema migrations between our app and OpenWebUI
- ⚠️ Slightly more complex setup than default SQLite

### Decision 3: 2FA via TOTP (Not SMS or Email Codes)
**Options Considered:**
- A) TOTP (Google Authenticator, Authy)
- B) SMS codes
- C) Email codes
- D) WebAuthn / Passkeys

**Decision:** Option A (TOTP)

**Rationale:**
- No SMS service costs or delivery issues
- More secure than email codes (email can be compromised)
- Widely adopted (most users already have authenticator app)
- Offline capability (TOTP works without network)

**Trade-offs Accepted:**
- ⚠️ Requires users to install authenticator app
- ⚠️ Users can lose access if they lose phone (mitigation: backup codes)
- ⚠️ Less user-friendly than SMS for non-technical users

### Decision 4: Admin-Invite Only (Not Self-Registration)
**Options Considered:**
- A) Self-registration with admin approval
- B) Admin-invite only (no public signup)
- C) Open self-registration

**Decision:** Option B (admin-invite only)

**Rationale:**
- Tighter security (no one can even attempt to register without invitation)
- Simpler workflow (admin controls entire process)
- Prevents spam/abuse (no public signup form)
- Aligns with internal tool use case (known user base)

**Trade-offs Accepted:**
- ⚠️ Admin must manually invite each user
- ⚠️ Cannot scale to large public user base
- ⚠️ Users cannot "discover" and sign up themselves

## Hypotheses to Validate

### Hypothesis 1: OpenWebUI 2-Role System Is Sufficient for Phase 1
**Statement:** EVI 360 specialists can effectively use the system with only Admin/User roles visible in OpenWebUI UI, while we enforce finer permissions (superuser, readonly) in backend code.

**Validation Method:**
- Deploy Phase 1 to 3-5 test users
- Collect feedback after 1 week of use
- Ask: "Do you need to see your specific role (superuser/readonly) in the UI, or is admin/user sufficient?"

**Success Criteria:** 80% of test users report no confusion about their permissions

**If False:** Proceed directly to Phase 2 custom JWT implementation (skip Phase 1 hybrid approach)

### Hypothesis 2: Invitation-Based Provisioning Adds Acceptable Admin Overhead
**Statement:** Admins can efficiently manage user provisioning via email invitations without needing self-registration for a user base of 10-50 users.

**Validation Method:**
- Time admin performing 5 user invitations
- Collect admin feedback on workflow pain points

**Success Criteria:**
- Invitation workflow < 3 minutes per user
- Admin reports no significant friction

**If False:** Consider adding admin bulk-invite feature (CSV upload) or self-registration with approval

### Hypothesis 3: Users Will Adopt 2FA Without Resistance
**Statement:** EVI 360 specialists are willing and able to set up Google Authenticator for 2FA, improving security without impacting adoption.

**Validation Method:**
- Deploy optional 2FA to test users
- Measure adoption rate after 2 weeks
- Collect feedback on setup difficulty

**Success Criteria:**
- 90%+ of test users successfully set up 2FA
- Adoption time < 5 minutes
- No reports of "too difficult" or "don't want to use app"

**If False:** Consider SMS-based 2FA or email codes as fallback

### Hypothesis 4: Backend Role Enforcement Prevents Permission Bypass
**Statement:** Enforcing role permissions in FastAPI (without modifying OpenWebUI UI) is sufficient to prevent users from accessing unauthorized features.

**Validation Method:**
- Security testing: Attempt to access admin endpoints as regular user
- Attempt to bypass OpenWebUI and call FastAPI directly
- Check audit logs for permission violations

**Success Criteria:**
- 0 successful permission bypasses in penetration testing
- All unauthorized attempts logged correctly

**If False:** Must add role checking at OpenWebUI level (requires forking OpenWebUI or contributing upstream)

### Hypothesis 5: Shared PostgreSQL Doesn't Cause Conflicts with OpenWebUI
**Statement:** Configuring OpenWebUI to use our PostgreSQL database (via DATABASE_URL) doesn't cause table name conflicts, migration issues, or performance problems.

**Validation Method:**
- Run OpenWebUI with DATABASE_URL pointing to evi_rag database
- Check for table name collisions
- Run our application's SQL migrations
- Monitor database performance

**Success Criteria:**
- No table name conflicts
- Our migrations run successfully
- Query performance remains acceptable (<100ms for auth queries)

**If False:** Isolate OpenWebUI into separate PostgreSQL schema or database

## Open Questions

### 1. Email Service Provider Selection
**Question:** Which email service should we use for invitations/resets/verification?

**Options:**
- A) SendGrid (easy setup, 100 emails/day free)
- B) AWS SES (requires AWS account, $0.10 per 1000 emails)
- C) Mailgun (25000 emails/month free, good API)
- D) Self-hosted SMTP (requires email server setup)

**Why it matters:** Affects setup complexity, cost, and email deliverability rates

**Who can answer:** You (budget/existing services) + Research (best option for EU deployment)

**Status:** ⏳ Pending - Need to understand existing EVI 360 infrastructure

### 2. Role Permission Matrix
**Question:** What specific permissions differ between admin, superuser, user, and readonly roles?

**Examples to clarify:**
- Can readonly users create chat sessions (or only view existing)?
- Can readonly users search guidelines/products?
- What advanced features do superusers get that regular users don't?
- Can superusers view other users' chats? Audit logs?

**Why it matters:** Determines backend permission logic complexity

**Who can answer:** You (product requirements)

**Status:** ⏳ Pending - Awaiting role permission specification from you

### 3. Account Lockout Policy
**Question:** After how many failed login attempts should we lock an account? Lockout duration?

**Options:**
- A) 5 attempts → 15-minute lockout
- B) 3 attempts → 30-minute lockout
- C) 10 attempts → 1-hour lockout
- D) No automatic lockout (rely on rate limiting only)

**Why it matters:** Balance security (prevent brute force) vs. user frustration (legitimate users locked out)

**Who can answer:** You (risk tolerance) + Security best practices research

**Status:** ⏳ Pending - Recommend Option A as starting point

### 4. Concurrent Session Limit
**Question:** Should we enforce a maximum number of concurrent sessions per user?

**Options:**
- A) No limit (allow unlimited devices)
- B) 5 concurrent sessions (recommended)
- C) 3 concurrent sessions (stricter)
- D) 1 session only (very strict, poor UX)

**Why it matters:** Security (prevents credential sharing) vs. UX (users have laptop + phone + tablet)

**Who can answer:** You (user behavior expectations)

**Status:** ⏳ Pending - Recommend Option B (5 sessions) with "logout all others" feature

### 5. 2FA Enforcement Policy
**Question:** Should 2FA be mandatory for all users or optional?

**Options:**
- A) Mandatory for all users
- B) Mandatory for admins/superusers, optional for regular users
- C) Optional for all users (encourage but don't require)
- D) Configurable per-user (admin decides)

**Why it matters:** Security vs. adoption friction

**Who can answer:** You (security requirements)

**Status:** ⏳ Pending - Recommend Option B (mandatory for elevated privileges)

### 6. Password Policy Requirements
**Question:** What password strength requirements should we enforce?

**Options:**
- A) Minimum 8 characters, no other requirements
- B) Minimum 12 characters, require uppercase + lowercase + number + special character
- C) Minimum 16 characters passphrase-style
- D) zxcvbn-based password strength scoring (reject weak passwords)

**Why it matters:** Security (prevent weak passwords) vs. UX (users forget complex passwords)

**Who can answer:** You (policy preference) + Security best practices

**Status:** ⏳ Pending - Recommend Option D (zxcvbn scoring, minimum strength 3/4)

### 7. EU Server Deployment Timeline
**Question:** When do you expect to deploy to EU server with HTTPS?

**Why it matters:**
- If soon (< 2 months): Should design for production from start
- If later (> 6 months): Can optimize for local development first

**Who can answer:** You (deployment timeline)

**Status:** ⏳ Pending - Impacts whether we prioritize local or production setup

## What I've Discovered That You Might Not Know

### Critical Finding 1: OpenWebUI 2FA Support Is Very Recent
**Discovery:** OpenWebUI TOTP 2FA was only merged in **December 2024** (discussion #16338). This is cutting-edge functionality.

**Implications:**
- May have bugs or incomplete features
- Documentation might be sparse
- Might require running `main` branch instead of stable release
- Should test thoroughly before relying on it

**Recommendation:** Validate OpenWebUI 2FA works in Phase 1 experiment before committing to it

### Critical Finding 2: OpenWebUI Email Verification Not Built-In
**Discovery:** OpenWebUI does not have native email verification for new user signups.

**Implications:**
- Must build custom email verification in Phase 2
- Requires adding verification token to user table
- Must send verification emails via FastAPI, not OpenWebUI

**Recommendation:** Phase 2 requirement - cannot use OpenWebUI's auth alone for email verification

### Critical Finding 3: Backend Currently Unprotected
**Discovery:** Your FastAPI endpoints (agent/api.py) do NOT currently validate JWT tokens from OpenWebUI.

**Implications:**
- Anyone with curl can bypass OpenWebUI and directly call your API
- User isolation doesn't exist (no user_id in sessions)
- Critical security gap for production deployment

**Recommendation:** Phase 1 MUST add JWT validation middleware (2-hour task)

### Critical Finding 4: Audit Logging Best Practices
**Discovery:** Security standards (SOC2, ISO 27001, HIPAA) require:
- Append-only audit logs (tamper-proof)
- Minimum 90-day retention
- Logging of administrator actions
- Regular log review and automated alerts

**Implications:**
- Need dedicated `audit_logs` table (separate from application logs)
- Cannot use rolling log files (must be database-backed)
- Should implement log integrity checks (cryptographic hashes)

**Recommendation:** Phase 3 requirement - audit logging is compliance-critical

### Critical Finding 5: GDPR Account Deletion Complexity
**Discovery:** GDPR-compliant deletion requires:
- 30-day grace period for account recovery
- Deletion from backups (or exclusion when restoring)
- Data export capability before deletion
- Audit trail of deletion (even though user is deleted)

**Implications:**
- Cannot simply `DELETE FROM users WHERE id = ?`
- Need "soft delete" with 30-day grace period
- Need data export endpoint (JSON download of all user data)

**Recommendation:** Phase 3 requirement - complex feature (3-5 days implementation)

### Critical Finding 6: Session Management Requires Refresh Tokens
**Discovery:** Best practice is access token (15 min) + refresh token (30 days) pattern.

**Implications:**
- Short-lived access tokens limit damage if stolen
- Refresh tokens enable "logout all devices" feature
- Must implement token blacklist for revoked sessions

**Recommendation:** Phase 2 requirement if implementing custom JWT (OpenWebUI handles this internally)

## Related Context

### Existing Features
- **FEAT-007**: OpenWebUI Web Interface - Already deployed, needs authentication integration
- **FEAT-008**: Advanced Memory Management - Uses sessions/messages tables (must integrate with user_id)
- **Current sessions table**: Has `user_id TEXT` field (ready for user identification)
- **Current messages table**: Links to sessions (automatic user isolation once sessions have user_id)

### Architecture Implications
**PostgreSQL Schema:**
```sql
-- Our existing tables (relevant to auth):
sessions (id, user_id, metadata, created_at, updated_at)  -- user_id currently NULL
messages (id, session_id, role, content, metadata)       -- linked to sessions

-- OpenWebUI will add (if DATABASE_URL configured):
user (id, email, password, role, ...)                    -- OpenWebUI manages
chat (id, user_id, title, ...)                           -- OpenWebUI chat history
message (id, chat_id, content, ...)                      -- OpenWebUI messages

-- We need to add (Phase 2):
users (id, email, password_hash, role, totp_secret, ...)  -- Our user table
invitations (id, email, token, role, expires_at, ...)     -- Invite tokens
audit_logs (id, user_id, event_type, ip_address, ...)    -- Security audit
sessions_tokens (id, user_id, refresh_token, ...)        -- If custom JWT
```

**Key Decision:** Do we use OpenWebUI's `user` table or create our own `users` table?
- **Option A**: Use OpenWebUI's `user` table, add our custom fields (role, totp_secret)
- **Option B**: Create separate `users` table, sync with OpenWebUI's `user` table
- **Recommendation**: Option A (simpler, avoids sync issues) - validate in Phase 1

### References
- [OpenWebUI Documentation](https://docs.openwebui.com/)
- [OpenWebUI 2FA Discussion #16338](https://github.com/open-webui/open-webui/discussions/16338)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI-Mail for Email Sending](https://github.com/sabuhish/fastapi-mail)
- [PyOTP for TOTP 2FA](https://github.com/pyauth/pyotp)
- [GDPR Right to Erasure Guidelines](https://gdpr-info.eu/art-17-gdpr/)

---

## Next Steps

**Immediate Actions:**
1. ✅ **You**: Provide role permission matrix (admin, superuser, user, readonly capabilities)
2. ⏳ **You**: Choose email service provider (SendGrid, AWS SES, Mailgun, or self-hosted)
3. ⏳ **You**: Decide on 2FA policy (mandatory for all? mandatory for admins only? optional?)
4. ⏳ **You**: Confirm EU server deployment timeline

**Phase 1 Validation Experiment (This Week):**
1. Enable OpenWebUI auth with shared PostgreSQL
2. Add FastAPI JWT validation middleware
3. Test with 2-3 users for 1 week
4. Validate Hypotheses 1, 4, and 5
5. Document findings and decision: proceed with hybrid approach or switch to custom JWT?

**Planning Phase (After PRD Approval):**
1. Run `/plan FEAT-013` to create architecture, acceptance criteria, testing strategy
2. Researcher agent investigates open questions
3. Create detailed implementation roadmap with milestones

**Status:** 🟡 Awaiting your input on open questions before proceeding to planning phase
