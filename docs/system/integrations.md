# External Integrations

**Last Updated:** 2025-10-24
**Status:** Template - Update for your project

## Overview

This document lists all external services, APIs, and integrations used by the project, including configuration details and dependencies.

## MCPs (Model Context Protocol)

### Archon (Optional)

**Purpose:** Knowledge management and task tracking

**Status:** Optional - not required for Phase 1

**Configuration:**
- MCP Server: `mcp__archon__*`
- Installation: [Link to Archon MCP docs]
- Connection: Configure in Claude Code settings

**Usage:**
- Researcher agent queries framework documentation
- Future: Task synchronization (Phase 3)
- Future: Session state persistence (Phase 3)

**See Also:** [CLAUDE.md](../../CLAUDE.md#archon-integration-optional)

---

### [Other MCP Name]

**Purpose:** [What this MCP provides]

**Configuration:** [Setup instructions]

**Usage:** [How it's used in project]

---

## External Services

### Service 1: [Name]

**Purpose:** [What this service does for us]

**Provider:** [Company/platform name]

**Documentation:** [Link to official docs]

**API Endpoint:** [Base URL if applicable]

**Authentication:**
- Method: [API Key / OAuth / JWT]
- Configuration: [Where credentials are stored]
- Environment Variable: `SERVICE_API_KEY`

**Rate Limits:**
- Free tier: [Limits]
- Paid tier: [Limits if applicable]

**Integration Points:**
- [Where in codebase this is used]
- [Which features depend on this]

**Fallback Strategy:**
- [What happens if service is unavailable]

---

### Service 2: [Name]

*Repeat template for each service*

---

## Third-Party Libraries

### Major Dependencies

| Library | Purpose | Version | License |
|---------|---------|---------|---------|
| [Name] | [What it does] | [X.Y.Z] | [MIT/Apache/etc.] |
| [Name] | [What it does] | [X.Y.Z] | [License] |

**Dependency Management:**
- Lock file: [package-lock.json / poetry.lock / Cargo.lock]
- Update policy: [How often dependencies are updated]
- Security: Dependabot enabled for vulnerability alerts

## Configuration

### Environment Variables

Required environment variables for integrations:

```bash
# Service 1
SERVICE_1_API_KEY=your_api_key_here
SERVICE_1_BASE_URL=https://api.service1.com

# Service 2
SERVICE_2_CLIENT_ID=your_client_id
SERVICE_2_CLIENT_SECRET=your_secret

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

**Setup:**
1. Copy `.env.example` to `.env`
2. Fill in your credentials
3. Never commit `.env` to git

### Configuration Files

**Location:** [Where config files live]

**Format:** [JSON / YAML / TOML]

**Example:**
```json
{
  "integrations": {
    "service1": {
      "enabled": true,
      "timeout": 5000
    }
  }
}
```

## Testing Integrations

### Mock Services

For testing, we mock external services:
- **Unit Tests:** Always mocked
- **Integration Tests:** Use test/sandbox environments when available
- **E2E Tests:** May use real services in staging

**Mock Data Location:** `tests/fixtures/integrations/`

### Test Credentials

**Available Test Accounts:**
- Service 1: test@example.com / test123
- Service 2: [Test account details]

**Test API Keys:**
- Stored in CI/CD secrets
- Different from production keys
- Limited permissions

## Monitoring

### Health Checks

**Endpoint:** `/health`

**Checks:**
- Database connectivity
- External service availability
- MCP connections (if used)

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "up",
    "service1": "up",
    "service2": "degraded"
  }
}
```

### Alerting

**Alerts configured for:**
- Service downtime
- Rate limit approaching
- Authentication failures
- Slow response times

## Cost Management

### Current Costs

| Service | Plan | Monthly Cost | Usage |
|---------|------|--------------|-------|
| [Service 1] | [Plan] | $X | [Usage details] |
| [Service 2] | [Plan] | $Y | [Usage details] |

**Total:** $X/month

### Cost Optimization

- [Strategy 1: e.g., caching to reduce API calls]
- [Strategy 2: e.g., using free tiers where possible]

## Security

### API Keys

- **Storage:** GitHub Secrets, environment variables
- **Rotation:** [Frequency and process]
- **Scope:** Minimal permissions principle

### Data Privacy

- **PII Handling:** [How user data is shared with services]
- **Compliance:** [GDPR, CCPA considerations]
- **Data Residency:** [Where data is processed/stored]

## Disaster Recovery

### Service Outages

**If Service 1 goes down:**
1. [Fallback strategy]
2. [User communication]
3. [Manual workaround if available]

**If Database is unavailable:**
1. [Backup restoration process]
2. [Estimated recovery time]

## Future Integrations

### Planned (Phase 2/3)

- [Integration name]: [Purpose and timeline]
- [Integration name]: [Purpose and timeline]

### Under Consideration

- [Integration name]: [Pros/cons, decision pending]

---

**Note:** Update this document when:
- New services are integrated
- API versions change
- Credentials are rotated
- Costs change significantly
- MCPs are added or removed
