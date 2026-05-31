#!/bin/bash
cd /home/pingmepls/projects/DailyDiet
git status -s
echo '---'
git diff --stat
echo '---'
git diff --cached --stat
echo '---'
git log -3 --oneline
