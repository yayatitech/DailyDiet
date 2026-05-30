#!/bin/bash
set -e
cd /home/pingmepls/projects/DailyDiet
rm -f .git/index.lock
git add -A
T=$(git write-tree)
P=$(git rev-parse HEAD)
N=$(git commit-tree "$T" -p "$P" -m 'Remove v1 legacy SPA and obsolete scripts')
git update-ref refs/heads/v2/python-stack "$N"
git push DailyDiet v2/python-stack
git log -1 --oneline
git status -s
rm -f /home/pingmepls/projects/DailyDiet/.commit_cleanup.sh
