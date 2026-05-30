#!/usr/bin/env bash
set -e
cd /home/pingmepls/projects/DailyDiet
export PATH="/home/pingmepls/.nvm/versions/node/v24.16.0/bin:$PATH"
rm -rf node_modules package-lock.json
npm install
npm run build
echo BUILD_OK
