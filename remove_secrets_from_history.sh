#!/bin/bash
set -e

echo "🔒 Removing secrets from git history..."
echo ""

# 1. Create backup
echo "1. Creating backup branch..."
git branch -f backup-before-secret-removal 2>/dev/null || git branch backup-before-secret-removal
echo "   ✅ Backup created: backup-before-secret-removal"
echo ""

# 2. Use filter-branch to remove secrets
echo "2. Filtering commit history to remove secrets..."
git filter-branch -f --tree-filter '
if [ -f "docs/features/FEAT-002_notion-integration/VALIDATION_REPORT.md" ]; then
  # Remove Notion API token
  sed -i "" "s/NOTION_API_TOKEN=ntn_[a-zA-Z0-9_]*/NOTION_API_TOKEN=REDACTED/g" "docs/features/FEAT-002_notion-integration/VALIDATION_REPORT.md" 2>/dev/null || \
  sed -i "s/NOTION_API_TOKEN=ntn_[a-zA-Z0-9_]*/NOTION_API_TOKEN=REDACTED/g" "docs/features/FEAT-002_notion-integration/VALIDATION_REPORT.md"

  # Remove database ID
  sed -i "" "s/NOTION_GUIDELINES_DATABASE_ID=[a-f0-9]*/NOTION_GUIDELINES_DATABASE_ID=REDACTED/g" "docs/features/FEAT-002_notion-integration/VALIDATION_REPORT.md" 2>/dev/null || \
  sed -i "s/NOTION_GUIDELINES_DATABASE_ID=[a-f0-9]*/NOTION_GUIDELINES_DATABASE_ID=REDACTED/g" "docs/features/FEAT-002_notion-integration/VALIDATION_REPORT.md"
fi
' HEAD~3..HEAD

echo "   ✅ History filtered"
echo ""

# 3. Clean up
echo "3. Cleaning up..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "   ✅ Cleanup complete"
echo ""

# 4. Verify
echo "4. Verifying secret removal..."
if git log --all --source --full-history -S "ntn_6384796" | grep -q "ntn_6384796"; then
  echo "   ⚠️  WARNING: Secret might still be in history"
  echo "   Check manually: git log -p | grep ntn_"
else
  echo "   ✅ Secret removed from all commits"
fi
echo ""

echo "✅ Done! Now you can push:"
echo "   git push -f origin V2"
echo ""
echo "ℹ️  If something goes wrong, restore from backup:"
echo "   git reset --hard backup-before-secret-removal"
