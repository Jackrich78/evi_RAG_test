# ⚠️ Supabase Connection Issue Detected

## Problem

Your DATABASE_URL hostname cannot be resolved:
```
db.kztmsmnxtwkqapzwxnso.supabase.co - Unknown host
```

This means either:
1. ❌ The Supabase project was paused/deleted
2. ❌ The connection string has the wrong hostname
3. ❌ Network/DNS issue

## How to Fix

### Step 1: Check Supabase Project Status

1. Go to https://app.supabase.com
2. Find your `evi-rag-system` project
3. Check if it shows as:
   - ✅ **Active** (green status)
   - ⏸️ **Paused** (needs to be resumed)
   - ❌ **Deleted** (need to create new one)

### Step 2: Get Correct Connection String

**If project is ACTIVE**:

1. In Supabase dashboard, click on your project
2. Go to: **Project Settings** → **Database**
3. Scroll to "Connection string" section
4. Select **URI** tab (NOT "Connection pooling")
5. Copy the EXACT string - it should look like:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```

**IMPORTANT**:
- The format might be different than what's in your .env!
- Make sure you copy from **"URI"** tab, not "Session" or "Transaction"
- Replace `[YOUR-PASSWORD]` with your actual database password

### Step 3: Update .env File

Replace line 13 in your `.env` with the correct connection string:

```bash
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

### Step 4: Test Connection Again

```bash
source venv/bin/activate
python3 tests/test_supabase_connection.py
```

## Common Mistakes

❌ **Wrong format**: Using "Session pooling" or "Transaction pooling" URL
✅ **Correct format**: Using "URI" connection string

❌ **Wrong tab**: Copying from "Connection pooling" section
✅ **Correct tab**: Copying from "Connection string" → "URI"

❌ **Paused project**: Free tier projects pause after inactivity
✅ **Active project**: Click "Resume" if paused

## Expected Connection String Format

Your connection string should follow ONE of these patterns:

**Pattern 1** (Direct connection):
```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Pattern 2** (Connection pooling - newer format):
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

**Pattern 3** (Transaction mode):
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

The hostname `db.kztmsmnxtwkqapzwxnso.supabase.co` in your .env doesn't match any of these patterns, which is suspicious.

## What to Check in Supabase Dashboard

1. **Project Status**: Is it green/active?
2. **Region**: Which region is it in? (eu-central-1, us-east-1, etc.)
3. **Connection String**: Copy the EXACT string from the dashboard
4. **Password**: Make sure you're using the correct database password

## Next Steps

1. ✅ Go to Supabase dashboard
2. ✅ Verify project is active
3. ✅ Get correct connection string from "URI" tab
4. ✅ Update `.env` file line 13
5. ✅ Re-run test script

Once the connection string is corrected, the test should work!
