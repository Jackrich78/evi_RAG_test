#!/usr/bin/env python3
"""
Quick diagnostic script to verify DATABASE_URL format.
Run this to check if your connection string looks correct.
"""

import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

def verify_database_url():
    """Verify the DATABASE_URL format and provide feedback."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in .env file!")
        return False

    print("=" * 60)
    print("DATABASE_URL Verification")
    print("=" * 60)

    # Parse the URL
    try:
        parsed = urlparse(database_url)

        print(f"\n📋 Parsed Components:")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * 10 if parsed.password else 'MISSING'}")
        print(f"   Hostname: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path.lstrip('/')}")

        # Verify components
        issues = []

        if parsed.scheme != "postgresql":
            issues.append("❌ Scheme should be 'postgresql'")
        else:
            print("   ✅ Scheme is correct")

        if not parsed.username:
            issues.append("❌ Username is missing")
        else:
            print(f"   ✅ Username is present: {parsed.username}")

        if not parsed.password:
            issues.append("❌ Password is missing")
        else:
            print(f"   ✅ Password is present ({len(parsed.password)} characters)")

        if not parsed.hostname:
            issues.append("❌ Hostname is missing")
        else:
            hostname = parsed.hostname
            print(f"\n🔍 Hostname Analysis: {hostname}")

            # Check hostname format
            if "supabase.co" in hostname:
                print("   ✅ Contains 'supabase.co'")

                # Check for common patterns
                if hostname.startswith("db.") and hostname.endswith(".supabase.co"):
                    print("   ✅ Direct connection format: db.[PROJECT-REF].supabase.co")
                    print("   📝 This is the OLD format - still valid")

                elif "pooler.supabase.com" in hostname:
                    print("   ✅ Pooled connection format: aws-0-[REGION].pooler.supabase.com")
                    print("   📝 This is the NEW format - preferred")

                else:
                    print("   ⚠️  Unusual Supabase hostname format")
                    print("   📝 Double-check this is correct from Supabase dashboard")

            else:
                print("   ❌ Does not contain 'supabase.co' or 'supabase.com'")
                issues.append("❌ Hostname doesn't look like a Supabase URL")

        if not parsed.port:
            issues.append("❌ Port is missing")
        elif parsed.port not in [5432, 6543]:
            print(f"   ⚠️  Unusual port: {parsed.port} (typically 5432 or 6543)")
        else:
            print(f"   ✅ Port is valid: {parsed.port}")

        if not parsed.path or parsed.path == "/":
            issues.append("❌ Database name is missing")
        else:
            db_name = parsed.path.lstrip('/')
            if db_name == "postgres":
                print(f"   ✅ Database name: {db_name}")
            else:
                print(f"   ⚠️  Unusual database name: {db_name} (typically 'postgres')")

        # Summary
        print("\n" + "=" * 60)
        if issues:
            print("❌ ISSUES FOUND:")
            for issue in issues:
                print(f"   {issue}")
            print("\n📝 Action Required:")
            print("   1. Go to Supabase dashboard")
            print("   2. Project Settings → Database")
            print("   3. Copy connection string from 'URI' tab")
            print("   4. Update DATABASE_URL in .env")
            return False
        else:
            print("✅ DATABASE_URL format looks correct!")
            print("\n📝 Next Step:")
            print("   Test the connection:")
            print("   python3 tests/test_supabase_connection.py")
            return True

    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False

if __name__ == "__main__":
    success = verify_database_url()
    exit(0 if success else 1)
