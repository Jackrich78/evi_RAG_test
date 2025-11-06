# FEAT-013: Authentication & User Management

**Status:** Exploring - Awaiting Input
**Created:** 2025-11-06

## Quick Links

- **[PRD](./prd.md)** - Full product requirements document with user stories, trade-offs, and hypotheses
- **[Deep Dive Findings](./DEEP_DIVE_FINDINGS.md)** - Research discoveries and missing considerations
- This README - Quick reference and status tracking

## TL;DR

Adding authentication to EVI 360 RAG system for 10-50 workplace safety specialists. Phased approach:
- **Phase 1** (Week 1): OpenWebUI auth + FastAPI token validation - VALIDATE APPROACH
- **Phase 2** (Weeks 2-4): Add invite-only provisioning, 2FA, email verification
- **Phase 3** (Weeks 5-6): GDPR compliance, audit logging, production polish

## Critical Discoveries

1. ⚠️ **Your FastAPI backend is currently unprotected** - anyone can curl it
2. 🔒 **OpenWebUI 2FA is brand new** (Dec 2024) - must test thoroughly
3. 📧 **Email verification not built into OpenWebUI** - must build custom
4. 👥 **Invite-only requires custom build** - no library provides this
5. 🇪🇺 **GDPR compliance is complex** - 30-day grace period, data export required
6. 🗄️ **OpenWebUI creates its own database** - can share your PostgreSQL

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth approach | OpenWebUI (Phase 1) → Hybrid (Phase 2) | Validate before committing |
| Database | Shared PostgreSQL | Single backup point, can query users |
| 2FA method | TOTP (Google Authenticator) | No SMS costs, more secure |
| Provisioning | Admin-invite only | Internal tool, tighter security |
| Role enforcement | Backend (FastAPI) | OpenWebUI only supports 2 roles in UI |

## Open Questions (Need Your Input)

### Critical (Blocks Phase 1)
1. **Role permission matrix** - What can each role do?
2. **Email service** - SendGrid, AWS SES, Mailgun, or self-hosted?

### Important (Can defer to Phase 2)
3. **2FA policy** - Mandatory for all? Admins only? Optional?
4. **Password policy** - Length/complexity requirements?
5. **Account lockout** - After how many failed attempts?
6. **Concurrent sessions** - Max sessions per user?
7. **EU server timeline** - When will you deploy with HTTPS?

## Files in This Feature

```
FEAT-013_authentication-and-user-management/
├── README.md                   # This file
├── prd.md                      # Full product requirements
├── DEEP_DIVE_FINDINGS.md       # Research discoveries
└── (Future files)
    ├── architecture.md         # After /plan command
    ├── acceptance.md           # Acceptance criteria
    ├── testing.md              # Test strategy
    └── research.md             # If researcher agent needed
```

## Next Actions

**For You:**
1. Review PRD and Deep Dive Findings
2. Answer critical questions (Q1, Q2)
3. Approve phased approach or request changes
4. Decide: Run Phase 1 experiment or skip to custom JWT?

**For Implementation:**
1. Once approved, run `/plan FEAT-013` to create architecture docs
2. Implement Phase 1 (4 hours work)
3. Test with users for 1 week
4. Decide on Phase 2 direction based on results

## Hypotheses to Validate

1. ✅ OpenWebUI 2-role UI is sufficient with backend enforcement
2. ✅ Invite workflow is efficient for 10-50 users
3. ✅ Users will adopt 2FA (TOTP) without friction
4. ✅ Backend role enforcement prevents permission bypasses
5. ✅ Shared PostgreSQL doesn't conflict with OpenWebUI

**Validation Method:** Phase 1 experiment with 3-5 test users for 1 week

## Key Trade-Offs

**Speed vs. Control:**
- OpenWebUI auth works in 1 hour (Phase 1)
- Custom FastAPI JWT takes 1-2 weeks but gives full control
- **Decision:** Start fast, enhance later if needed

**Database Isolation vs. Simplicity:**
- Separate SQLite: Simpler but data in 2 places
- Shared PostgreSQL: One DB but OpenWebUI controls schema
- **Decision:** Shared PostgreSQL (can query users from Python)

**Security vs. UX:**
- Mandatory 2FA: More secure but higher friction
- Optional 2FA: Better UX but less secure
- **Decision:** Pending your input (recommend mandatory for admins)

## Related Features

- **FEAT-007**: OpenWebUI Web Interface (already deployed)
- **FEAT-008**: Advanced Memory (sessions/messages tables ready for user_id)

---

**Status:** 🟡 Awaiting your input on critical questions before proceeding to planning phase.

**Contact:** Respond with answers to open questions to unblock Phase 1 implementation.
