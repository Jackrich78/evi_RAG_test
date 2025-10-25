# SOP: Code Style and Quality

**Purpose:** Maintain consistent, readable, and maintainable code across the project
**Applies To:** All source code files
**Last Updated:** 2025-10-24

## Overview

We prioritize code readability and maintainability over cleverness. Code is written once but read many times, so clarity is paramount. Automated tools enforce style where possible.

## General Principles

### Readability First
- Clear variable names over short names
- Simple solutions over complex ones
- Comments explain "why", code shows "how"
- Consistent formatting project-wide

### DRY (Don't Repeat Yourself)
- Extract repeated logic into functions
- Use shared utilities and helpers
- Create abstractions when beneficial (but not prematurely)

### YAGNI (You Aren't Gonna Need It)
- Don't add features "just in case"
- Build what's needed now
- Refactor when requirements change

### SOLID Principles
- Single Responsibility: One purpose per function/class
- Open/Closed: Extend behavior without modifying existing code
- Liskov Substitution: Subtypes should be substitutable
- Interface Segregation: Many specific interfaces over one general
- Dependency Inversion: Depend on abstractions, not concretions

## Naming Conventions

### Variables & Functions

**JavaScript/TypeScript:**
```typescript
// Variables: camelCase
const userName = 'John';
const isAuthenticated = true;

// Functions: camelCase, verb-first
function getUserById(id: string) { }
function validateEmail(email: string): boolean { }

// Classes: PascalCase
class UserService { }

// Constants: UPPER_SNAKE_CASE
const MAX_LOGIN_ATTEMPTS = 3;
const API_BASE_URL = 'https://api.example.com';

// Private members: prefix with _
class Auth {
  private _tokenCache: Map<string, string>;
}
```

**Python:**
```python
# Variables: snake_case
user_name = "John"
is_authenticated = True

# Functions: snake_case, verb_first
def get_user_by_id(user_id: str):
    pass

def validate_email(email: str) -> bool:
    pass

# Classes: PascalCase
class UserService:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_LOGIN_ATTEMPTS = 3
API_BASE_URL = "https://api.example.com"

# Private members: prefix with _
class Auth:
    def __init__(self):
        self._token_cache = {}
```

### Files & Directories

- **Source files:** Match primary class/function name
  - `UserService.ts`, `user_service.py`
- **Test files:** Match source + `.test` or `_test`
  - `UserService.test.ts`, `user_service_test.py`
- **Directories:** lowercase, hyphen-separated
  - `user-management/`, `api-endpoints/`

## File Organization

### File Length
- **Ideal:** <250 lines
- **Maximum:** 500 lines
- If longer, split into multiple files

### Import Organization

**JavaScript/TypeScript:**
```typescript
// 1. External dependencies
import React from 'react';
import { useAuth } from 'third-party-lib';

// 2. Internal modules
import { UserService } from '@/services/UserService';
import { validateEmail } from '@/utils/validators';

// 3. Relative imports
import { Button } from '../components/Button';
import './styles.css';
```

**Python:**
```python
# 1. Standard library
import os
import sys
from typing import List, Optional

# 2. Third-party
import requests
from fastapi import FastAPI

# 3. Local/project
from services.user_service import UserService
from utils.validators import validate_email
```

## Function Design

### Function Length
- **Ideal:** <20 lines
- **Maximum:** 50 lines
- One function = one responsibility

### Function Signature
```typescript
// Good: Clear purpose, limited parameters
function createUser(name: string, email: string): User {
  // ...
}

// Better: Use object for many parameters
interface CreateUserParams {
  name: string;
  email: string;
  role?: string;
  metadata?: Record<string, unknown>;
}

function createUser(params: CreateUserParams): User {
  // ...
}

// Bad: Too many parameters
function createUser(name, email, role, age, address, phone, ...): User {
  // ...
}
```

### Return Early
```typescript
// Good: Early returns reduce nesting
function processUser(user: User): Result {
  if (!user) return { error: 'User not found' };
  if (!user.isActive) return { error: 'User inactive' };

  return { success: true, data: user };
}

// Bad: Nested conditions
function processUser(user: User): Result {
  if (user) {
    if (user.isActive) {
      return { success: true, data: user };
    } else {
      return { error: 'User inactive' };
    }
  } else {
    return { error: 'User not found' };
  }
}
```

## Comments & Documentation

### When to Comment

**Do comment:**
- **Why** decisions were made
- Complex algorithms or business logic
- Workarounds for bugs or limitations
- Public APIs (JSDoc, docstrings)

**Don't comment:**
- **What** the code does (code should be self-explanatory)
- Obvious operations
- Dead code (delete instead)

### Good vs. Bad Comments

```typescript
// Bad: States the obvious
// Set user name to "John"
userName = "John";

// Good: Explains why
// Use hardcoded name for demo account (required by QA)
userName = "John";

// Bad: Commented-out code
// const oldFunction = () => { ... }

// Good: Explains complex logic
// Binary search: O(log n) performance required for large datasets
// Dataset can be 100k+ items based on client requirements
function binarySearch(arr: number[], target: number): number {
  // ...
}
```

### Documentation Strings

**TypeScript (JSDoc):**
```typescript
/**
 * Authenticates a user with email and password
 *
 * @param email - User's email address
 * @param password - Plain text password (will be hashed)
 * @returns Authentication token on success
 * @throws {AuthError} If credentials are invalid
 *
 * @example
 * const token = await authenticateUser('user@example.com', 'password123');
 */
async function authenticateUser(email: string, password: string): Promise<string> {
  // ...
}
```

**Python (Docstrings):**
```python
def authenticate_user(email: str, password: str) -> str:
    """
    Authenticates a user with email and password.

    Args:
        email: User's email address
        password: Plain text password (will be hashed)

    Returns:
        Authentication token on success

    Raises:
        AuthError: If credentials are invalid

    Example:
        >>> token = authenticate_user('user@example.com', 'password123')
    """
    pass
```

## Error Handling

### Exceptions vs. Return Values

**Use exceptions for:**
- Unexpected errors
- Conditions caller can't reasonably check
- Critical failures

**Use return values for:**
- Expected failures (validation errors)
- Business logic conditions
- Optional operations

```typescript
// Good: Exception for unexpected error
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch user: ${response.status}`);
  }
  return response.json();
}

// Good: Return value for expected validation
function validatePassword(password: string): ValidationResult {
  if (password.length < 8) {
    return { valid: false, error: 'Password too short' };
  }
  return { valid: true };
}
```

### Error Messages

- Be specific: "Email is required" not "Invalid input"
- Be actionable: "Password must be at least 8 characters" not "Bad password"
- Don't expose sensitive details: "Invalid credentials" not "Email not found in database"

## Code Formatting

### Automated Formatting (Phase 2)

PostToolUse hook will auto-format on save using:
- **JavaScript/TypeScript:** Prettier + ESLint
- **Python:** Black + Ruff
- **Rust:** rustfmt
- **Go:** gofmt

### Manual Standards (Phase 1)

**Indentation:** 2 spaces (JS/TS) or 4 spaces (Python)
**Line length:** 80-100 characters max
**Trailing commas:** Yes (easier diffs)
**Semicolons:** Consistent with project (ESLint enforces)

```typescript
// Good: Readable, consistent
const user = {
  name: 'John',
  email: 'john@example.com',
  role: 'admin',
};

// Bad: Inconsistent formatting
const user={name:"John",email:"john@example.com",role:"admin"}
```

## Anti-Patterns to Avoid

### Magic Numbers
```typescript
// Bad
if (user.loginAttempts > 3) { lockAccount(); }

// Good
const MAX_LOGIN_ATTEMPTS = 3;
if (user.loginAttempts > MAX_LOGIN_ATTEMPTS) { lockAccount(); }
```

### Deep Nesting
```typescript
// Bad: Pyramid of doom
if (user) {
  if (user.isActive) {
    if (user.hasPermission('admin')) {
      // ...
    }
  }
}

// Good: Early returns
if (!user) return;
if (!user.isActive) return;
if (!user.hasPermission('admin')) return;
// ...
```

### God Objects/Functions
- Functions that do too many things
- Classes with too many responsibilities
- Split into smaller, focused units

### Premature Optimization
- Optimize when profiling shows bottlenecks
- Readable code first, fast code second
- "Premature optimization is the root of all evil" - Donald Knuth

## Related Documentation

- [testing-strategy.md](testing-strategy.md) - Test code style
- [git-workflow.md](git-workflow.md) - Commit style
- Language-specific style guides (link external guides)

---

**This SOP is enforced by:** Code review, formatters (Phase 2), linters (Phase 2)
