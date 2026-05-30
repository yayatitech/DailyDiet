#!/bin/bash
set -e
cd /home/pingmepls/projects/DailyDiet

# Drop accidental helper scripts from the commit
git reset HEAD -- .fixup.sh .commit_cleanup.sh 2>/dev/null || true
rm -f .fixup.sh .commit_cleanup.sh .start-db.sh .start-web.sh

git add -A
git reset HEAD -- .start-db.sh .start-web.sh 2>/dev/null || true
rm -f .start-db.sh .start-web.sh

git status -s

T=$(git write-tree)
P=$(git rev-parse HEAD)
N=$(git commit-tree "$T" -p "$P" -m "$(cat <<'EOF'
Add meal items, recipe catalog, and fix bcrypt auth crash

Split slot meals into per-item rows with optional recipe links from a
shared catalog. Adds recipe CRUD API, seeds recipe-catalog.json, updates
requirements/docs, and replaces passlib with bcrypt to fix 500 errors
when auto-creating the dev user.
EOF
)")
git update-ref refs/heads/v2/python-stack "$N"
git push DailyDiet v2/python-stack
git log -1 --oneline
git status -s
