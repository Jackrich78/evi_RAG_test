# Database Schema

**Last Updated:** 2025-10-24
**Status:** Template - Update for your project

## Overview

*This document describes the database schema, tables, relationships, and data model. Update when you implement your database.*

**Database Type:** [PostgreSQL / MySQL / MongoDB / etc.]
**ORM/Query Builder:** [Prisma / TypeORM / SQLAlchemy / etc.]

## Schema Diagram

```
[Add ER diagram or schema visualization]

Example:
users (1) ──< (N) posts
users (1) ──< (N) sessions
```

## Tables

### Table: `users`

**Purpose:** Store user accounts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| created_at | TIMESTAMP | NOT NULL | Account creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `email`
- INDEX on `created_at` (for sorting/filtering)

---

### Table: `[table_name]`

*Add your tables here*

## Relationships

### One-to-Many

- `users` (1) → `sessions` (N): One user can have multiple sessions
- `users` (1) → `posts` (N): One user can create multiple posts

### Many-to-Many

- `users` ↔ `roles` via `user_roles` join table

## Migrations

**Migration Tool:** [Name of migration tool]

**Migration Files Location:** [e.g., `db/migrations/`]

**Running Migrations:**
```bash
[Command to run migrations]
# Example: npm run migrate
```

**Creating Migrations:**
```bash
[Command to create migration]
# Example: npm run migrate:create add_users_table
```

## Seeding

**Seed Data Location:** [e.g., `db/seeds/`]

**Running Seeds:**
```bash
[Command to seed database]
# Example: npm run db:seed
```

## Data Integrity

### Constraints

- **Foreign Keys:** Enabled with CASCADE/RESTRICT as appropriate
- **NOT NULL:** Required fields enforce NOT NULL constraint
- **UNIQUE:** Email addresses, usernames must be unique
- **CHECK:** Custom validation (e.g., age > 0)

### Triggers

*Document any database triggers*

Example:
- `updated_at` trigger: Auto-updates timestamp on row modification

## Performance

### Indexes

*List important indexes for performance*

- Users email lookup: INDEX on `users.email`
- Posts by user: INDEX on `posts.user_id`
- Recent posts: INDEX on `posts.created_at DESC`

### Query Optimization

*Document slow queries and optimization strategies*

## Backup & Recovery

**Backup Schedule:** [Frequency and retention]

**Backup Location:** [Where backups are stored]

**Recovery Process:**
1. [Step to restore from backup]
2. [Verification steps]

## Security

- **Encryption at Rest:** [Yes/No, method]
- **Encryption in Transit:** [SSL/TLS configuration]
- **Access Control:** [Who can access database]
- **Sensitive Data:** [How PII is handled]

## Development

**Local Database Setup:**
```bash
[Commands to setup local database]
# Example: docker-compose up -d postgres
```

**Test Database:**
- Separate test database for running tests
- Cleaned/reset before each test suite

---

**Note:** Update this document when:
- Tables are added, modified, or removed
- Indexes change
- Relationships change
- Migration process changes
