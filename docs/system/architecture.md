# System Architecture - EVI 360 RAG

**Last Updated:** 2025-10-25
**Status:** Phase 1-2 Complete, Phase 3+ In Planning

## Overview

The EVI 360 RAG system is an intelligent assistant for workplace safety specialists that provides **tiered guideline access** (Summary → Key Facts → Details), **product recommendations**, and operates entirely in **Dutch language**.

This document describes the architecture as implemented in **Phases 1-2** (Infrastructure + Data Models), with planned components for **Phases 3-8** clearly marked.

## Architecture Goals

- **Rapid Information Access**: 3-tier guideline hierarchy enables quick triage or deep dives as needed
- **Dutch Language First**: Native Dutch support for full-text search and agent responses
- **Unlimited Scale**: Local PostgreSQL eliminates cloud storage limits for large knowledge bases
- **Conversation Context**: Multi-agent system (planned Phase 5) maintains query state across interactions
- **Product Integration**: Connect safety guidelines with relevant EVI 360 equipment and services
- **Maintainability**: Separation of concerns across ingestion, storage, and agent layers

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Interface                              │
│                    (CLI / API / Web - Future)                      │
└────────────────────────────────┬─────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Layer (Phase 5 - Planned)               │
│                                                                   │
│  ┌──────────────────────┐      ┌───────────────────────────┐  │
│  │ Intervention         │      │   Research Agent          │  │
│  │ Specialist Agent     │◄─────│   (Tool for Specialist)   │  │
│  │                      │      │                           │  │
│  │ - Dutch responses    │      │ - Tier traversal (1→2→3)  │  │
│  │ - Product recs       │      │ - Vector search           │  │
│  │ - Context management │      │ - Graph queries           │  │
│  └──────────────────────┘      │ - Product lookup          │  │
│                                  └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│              Storage Layer (Phase 1-2 ✅ COMPLETE)               │
│                                                                   │
│  ┌──────────────────────────┐    ┌────────────────────────────┐ │
│  │ PostgreSQL 17            │    │   Neo4j 5.26.1            │ │
│  │ + pgvector 0.8.1         │    │   + APOC                  │ │
│  │ (Docker)                 │    │   (Docker)                │ │
│  │                          │    │                            │ │
│  │ - documents              │    │ - Guideline relationships │ │
│  │ - chunks (with tier)     │    │ - Product connections     │ │
│  │ - products               │    │ - Knowledge graph         │ │
│  │ - sessions/messages      │    │ - Temporal data           │ │
│  │ - Vector embeddings      │    │                            │ │
│  │ - Dutch full-text search │    │                            │ │
│  └──────────────────────────┘    └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  ↑
┌─────────────────────────────────────────────────────────────────┐
│            Ingestion Layer (Phase 3-4 - Planned)                 │
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────────────────┐ │
│  │ Notion Ingestion │         │   Product Scraping           │ │
│  │                  │         │                               │ │
│  │ - Fetch guidelines│        │ - Scrape EVI 360 site        │ │
│  │ - Detect tiers   │         │ - AI categorization          │ │
│  │ - Chunk by tier  │         │ - Compliance tag generation  │ │
│  │ - Generate embeds│         │ - Embed products             │ │
│  └──────────────────┘         └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                ↑                             ↑
            Notion API                  EVI 360 Website
```

## Components

### Component 1: [Name]

**Purpose:** [What this component does]

**Responsibilities:**
- [Responsibility 1]
- [Responsibility 2]

**Technology:** [Languages, frameworks, libraries used]

**Location:** [Where code lives: e.g., `src/server/`]

### Component 2: [Name]

**Purpose:** [What this component does]

**Responsibilities:**
- [Responsibility 1]
- [Responsibility 2]

**Technology:** [Stack details]

**Location:** [Code location]

## Data Flow

1. **User Request:** [How requests enter the system]
2. **Processing:** [How data is processed]
3. **Storage:** [How data is persisted]
4. **Response:** [How results are returned]

## Integration Points

### External Services

**Service 1: [Name]**
- **Purpose:** [Why we integrate]
- **Documentation:** [Link]
- **Configuration:** [Where config lives]

**Service 2: [Name]**
- **Purpose:** [Integration purpose]
- **Documentation:** [Link]
- **Configuration:** [Config location]

### Internal APIs

*Document internal APIs if multiple services*

## Security Architecture

- **Authentication:** [How users are authenticated]
- **Authorization:** [How permissions are managed]
- **Data Protection:** [Encryption, sanitization approach]
- **Secrets Management:** [How secrets are stored]

## Scalability

**Current Scale:**
- Users: [Number or "small", "medium", "large"]
- Requests: [Requests per second/minute]
- Data: [Data volume]

**Scaling Strategy:**
- [How to scale horizontally/vertically]
- [Bottlenecks and mitigation]

## Monitoring & Observability

**Logging:**
- [Where logs go]
- [What gets logged]

**Metrics:**
- [What metrics are tracked]
- [Where metrics are stored]

**Alerting:**
- [What triggers alerts]
- [Who gets notified]

## Deployment

**Environments:**
- **Development:** [Local setup]
- **Staging:** [Pre-production environment]
- **Production:** [Live environment]

**Deployment Process:**
- [How code gets deployed]
- [CI/CD pipeline details]

## Technology Stack

See [stack.md](stack.md) for detailed technology choices and versions.

## Architecture Decisions

Major architectural decisions are documented as ADRs in feature-specific planning docs:
- See `docs/features/FEAT-XXX/architecture.md` for feature-level decisions
- This document covers system-wide architecture only

## Evolution

*Document how architecture has changed over time*

**Version 1.0 (2025-10-24):**
- Initial template setup
- Phase 1: Planning & Documentation focus

**Future:**
- Phase 2: Add implementation components
- Phase 3: Add automation and profiles

---

**Note:** Update this document when:
- Major components are added or removed
- Integration points change
- Technology stack changes significantly
- Deployment process changes
