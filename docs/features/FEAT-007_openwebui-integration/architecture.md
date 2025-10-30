# Architecture Decision: OpenWebUI Integration

**Feature ID:** FEAT-007
**Decision Date:** 2025-10-30
**Status:** Proposed
**Decider:** Planner Agent

## Context

EVI 360 RAG system currently provides API endpoints for retrieving workplace safety guidelines and product recommendations. To improve accessibility for safety specialists, we need a chat interface that allows natural language queries instead of direct API calls. OpenWebUI provides a proven platform for building custom AI assistants with RAG capabilities.

**Key Requirements:**
- Natural language query interface for Dutch-language safety guidelines
- Real-time access to 3-tier guideline system (Summary/Key Facts/Details)
- Product catalog integration with compliance tags
- Multi-turn conversation support with context retention
- Secure authentication and session management
- Deployment alongside existing FastAPI backend

**Constraints:**
- Must integrate with existing PostgreSQL database (Neon)
- Must support Docker deployment (production and development)
- Must handle Dutch language queries effectively
- API response time <2 seconds for guideline retrieval
- Support for multiple concurrent users (10+ simultaneous sessions)

## Options Considered

### Option 1: OpenWebUI Standalone with API Integration

**Description:**
Deploy OpenWebUI as a separate Docker container that connects to our FastAPI backend via HTTP REST API. OpenWebUI handles UI, conversation management, and LLM orchestration while delegating all guideline/product retrieval to existing endpoints.

**Architecture:**
```
User → OpenWebUI (port 3000) → FastAPI Backend (port 8000) → PostgreSQL
                ↓
            OpenAI/Anthropic API
```

**Implementation Steps:**
1. Deploy OpenWebUI container with custom configuration
2. Create custom RAG pipeline that calls FastAPI endpoints
3. Configure OpenAI/Claude models via API keys
4. Implement authentication passthrough or shared session store
5. Add Docker Compose orchestration for both services

**Pros:**
- Clean separation of concerns (UI vs. backend logic)
- Minimal changes to existing FastAPI codebase
- Easy to swap UI layer if needed
- OpenWebUI handles conversation state management
- Built-in features: user management, chat history, model switching

**Cons:**
- Additional network latency (OpenWebUI → FastAPI → DB)
- Need to maintain two separate services
- Authentication complexity (coordinate between services)
- Potential for API versioning conflicts
- Higher resource consumption (two containers)

**Cost/Effort:**
- Development: 3-4 days
- Maintenance: Medium (two codebases to monitor)
- Infrastructure: Medium (additional container resources)

---

### Option 2: OpenWebUI Embedded with Direct Database Access

**Description:**
Integrate OpenWebUI as an embedded module within the FastAPI application, allowing it to directly access the PostgreSQL database for guideline retrieval. Replace REST API calls with direct database queries.

**Architecture:**
```
User → FastAPI + OpenWebUI (port 8000) → PostgreSQL
                ↓
            OpenAI/Anthropic API
```

**Implementation Steps:**
1. Install OpenWebUI as Python package dependency
2. Mount OpenWebUI routes within FastAPI application
3. Create custom RAG functions that query PostgreSQL directly
4. Share SQLAlchemy session/connection pool
5. Unify authentication using FastAPI middleware

**Pros:**
- Single deployment unit (simplified DevOps)
- Reduced latency (no HTTP overhead between services)
- Shared authentication and session management
- Easier to maintain consistent data models
- Lower resource consumption

**Cons:**
- Tight coupling between UI and backend
- Complex integration (OpenWebUI not designed for embedding)
- Harder to scale UI and API independently
- Risk of dependency conflicts (OpenWebUI may require different versions)
- Limited by OpenWebUI's architecture assumptions

**Cost/Effort:**
- Development: 5-6 days (integration complexity)
- Maintenance: High (tightly coupled systems)
- Infrastructure: Low (single container)

---

### Option 3: Custom Lightweight Chat UI with FastAPI Backend

**Description:**
Build a minimal custom chat interface (React/Vue + WebSocket) that connects to our existing FastAPI backend. Implement conversation management and LLM orchestration using Pydantic AI within FastAPI.

**Architecture:**
```
User → Custom UI (port 3000) → FastAPI + Pydantic AI (port 8000) → PostgreSQL
                                        ↓
                                OpenAI/Anthropic API
```

**Implementation Steps:**
1. Create simple chat UI with React/Vite
2. Add WebSocket endpoint to FastAPI for real-time chat
3. Implement conversation context management using Pydantic AI
4. Build RAG pipeline using existing database models
5. Add chat history storage to PostgreSQL

**Pros:**
- Full control over UI/UX and features
- Optimized for EVI 360's specific workflows
- Clean separation with defined API contracts
- Leverage existing FastAPI expertise
- No third-party UI dependencies to maintain

**Cons:**
- Significant development effort (build everything from scratch)
- Missing OpenWebUI features: prompt library, model switching, user management
- Ongoing UI maintenance burden
- Need frontend expertise for React/Vue development
- Longer time to production

**Cost/Effort:**
- Development: 7-10 days
- Maintenance: High (custom UI code)
- Infrastructure: Medium (two containers)

## Comparison Matrix

| Criteria | Option 1: Standalone OpenWebUI | Option 2: Embedded OpenWebUI | Option 3: Custom UI |
|----------|-------------------------------|------------------------------|---------------------|
| **Feasibility** | High - proven integration pattern | Medium - non-standard use of OpenWebUI | High - standard web app pattern |
| **Performance** | Medium - extra network hop (50-100ms) | High - direct DB access | High - optimized for use case |
| **Maintainability** | High - clear boundaries, standard deployment | Low - tight coupling, complex dependencies | Medium - full control but more code |
| **Cost** | Low - use existing tools | Low - single deployment | Medium - frontend development time |
| **Complexity** | Low - minimal custom code | High - deep integration work | Medium - standard stack |
| **Community Support** | High - active OpenWebUI community | Low - unusual integration approach | Medium - standard React/FastAPI |
| **Integration Ease** | High - RESTful APIs well-documented | Medium - requires OpenWebUI internals knowledge | High - full control over integration |

**Scoring:**
- Option 1: 6/7 criteria rated Medium-High → **Score: 85%**
- Option 2: 4/7 criteria rated Low-Medium → **Score: 55%**
- Option 3: 5/7 criteria rated Medium-High → **Score: 70%**

## Decision

**Recommended Approach:** **Option 1 - OpenWebUI Standalone with API Integration**

**Rationale:**

1. **Fastest Time to Value:** OpenWebUI provides production-ready chat UI, authentication, and conversation management out of the box. This allows focus on RAG pipeline optimization rather than UI development.

2. **Proven Architecture:** Microservices pattern with UI and API separation is well-established and aligns with modern deployment practices. Clear boundaries make debugging and scaling easier.

3. **Low Risk:** Minimal changes to existing FastAPI backend reduce risk of regression. If OpenWebUI doesn't meet needs, easy to swap with custom UI later.

4. **Feature-Rich:** OpenWebUI includes features that would take weeks to build: model switching, prompt templates, chat history, user management, document upload UI.

5. **Dutch Language Support:** OpenWebUI works with any LLM that supports Dutch (Claude, GPT-4) without language-specific modifications.

**Trade-offs Accepted:**
- Additional network latency (50-100ms) is acceptable for chat use case
- Resource overhead of second container is minimal with modern Docker deployment
- Authentication complexity manageable with shared JWT tokens or session store

**Risk Mitigation:**
- Start with shared Redis session store for authentication
- Implement API response caching to reduce latency
- Monitor performance and optimize API calls if needed
- Document API contracts clearly for future UI alternatives

## Spike Plan

**Objective:** Validate OpenWebUI integration with FastAPI backend and measure performance.

**Duration:** 1.5 days

### Step 1: Environment Setup (2 hours)
- Clone OpenWebUI repository
- Create Docker Compose file with OpenWebUI + existing FastAPI + PostgreSQL
- Configure environment variables (API keys, database connection)
- Verify all services start and can communicate

**Success Criteria:**
- All containers running without errors
- OpenWebUI accessible at http://localhost:3000
- FastAPI accessible at http://localhost:8000
- Health checks pass for all services

---

### Step 2: Basic API Integration (3 hours)
- Create custom RAG function in OpenWebUI that calls FastAPI `/query` endpoint
- Test simple query: "Wat zijn de richtlijnen voor werken op hoogte?" (What are guidelines for working at height?)
- Verify response returns tier 1 summary correctly
- Measure end-to-end latency

**Success Criteria:**
- OpenWebUI successfully calls FastAPI endpoint
- Dutch query returns relevant guideline summary
- Latency <2 seconds for simple queries
- Response formatted correctly in chat UI

---

### Step 3: Multi-Turn Conversation (3 hours)
- Implement conversation context retention using OpenWebUI's history
- Test follow-up queries: "Geef me meer details" (Give me more details)
- Verify tier 2/3 guidelines retrieved based on context
- Test product recommendations in conversation flow

**Success Criteria:**
- Follow-up questions retrieve correct tier level
- Conversation context maintained across 3+ turns
- Product recommendations integrated naturally
- No context confusion between different guideline topics

---

### Step 4: Authentication & Session Management (2 hours)
- Implement shared authentication mechanism (JWT or Redis session)
- Test login flow and session persistence
- Verify user-specific chat history
- Test concurrent sessions (2+ users)

**Success Criteria:**
- Users can authenticate and access chat
- Sessions persist across page reloads
- Chat history correctly scoped to user
- No session conflicts with concurrent users

---

### Step 5: Performance Testing & Documentation (2 hours)
- Run load test: 10 concurrent users, 5 queries each
- Measure P95 latency and error rates
- Document integration architecture and configuration
- Create deployment guide for production

**Success Criteria:**
- P95 latency <3 seconds under load
- Zero errors with 10 concurrent users
- Architecture diagram created
- Deployment steps documented

**Spike Deliverables:**
1. Working Docker Compose configuration
2. Custom RAG pipeline code for OpenWebUI
3. Performance test results (latency, concurrency)
4. Integration architecture diagram
5. Deployment documentation

**Go/No-Go Decision Criteria:**
- ✅ P95 latency <3 seconds → Proceed with Option 1
- ❌ Latency >5 seconds → Evaluate Option 3 (custom UI)
- ✅ Dutch queries work accurately → Proceed
- ❌ Frequent authentication issues → Re-evaluate session strategy

---

**Next Steps After Spike:**
1. Review spike results with team
2. If successful: proceed to full implementation planning
3. Create detailed technical specifications for RAG pipeline
4. Plan production deployment strategy (CI/CD, monitoring)
5. Document API contracts for OpenWebUI ↔ FastAPI integration
