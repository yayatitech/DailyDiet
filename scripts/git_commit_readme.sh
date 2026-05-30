#!/usr/bin/env bash
set -e
cd /home/pingmepls/projects/DailyDiet
git add README.md
git commit -F .commitmsg
rm -f .commitmsg
git push DailyDiet master
git status
