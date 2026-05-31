#!/bin/bash
set -e
cd /home/pingmepls/projects/DailyDiet

# Remove temp helper scripts from repo and disk
for f in .git-status.sh .git-commit.sh .start-web.sh .start-db.sh .fixup.sh .rm-helper.sh; do
  git reset HEAD -- "$f" 2>/dev/null || true
  rm -f "$f"
done

git add \
  apps/web/src/App.tsx \
  apps/web/src/MealSlotEditor.tsx \
  apps/web/src/MealSlotViewer.tsx \
  apps/web/src/RecipeLink.tsx \
  apps/web/src/styles.css \
  docs/REQUIREMENTS.md

# Include tests/config if present
git add apps/web/package.json apps/web/vite.config.ts apps/web/vitest.config.ts 2>/dev/null || true
git add apps/web/src/api.ts apps/web/src/api.test.ts apps/web/src/MealSlotEditor.test.ts 2>/dev/null || true

git status -s > /tmp/dd-commit-status.txt

T=$(git write-tree)
P=$(git rev-parse HEAD)
N=$(git commit-tree "$T" -p "$P" -m "Add View and Edit interaction modes to web app" -m "Default View mode shows read-only meals, recipe links, and slot checkboxes. Edit mode enables meal and notes editing and hides checkboxes. Persist mode in localStorage; add FR-25 and FR-26 to requirements.")
git update-ref refs/heads/v2/python-stack "$N"

git log -1 --oneline > /tmp/dd-commit-log.txt
git diff-tree --no-commit-id --name-only -r HEAD > /tmp/dd-commit-files.txt
git status -s > /tmp/dd-commit-status-after.txt

cat /tmp/dd-commit-log.txt
echo "---files---"
cat /tmp/dd-commit-files.txt
echo "---status---"
cat /tmp/dd-commit-status-after.txt
