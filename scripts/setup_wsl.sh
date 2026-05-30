#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  # shellcheck disable=SC1090
  source "$NVM_DIR/nvm.sh"
else
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  # shellcheck disable=SC1090
  source "$NVM_DIR/nvm.sh"
fi

nvm install --lts
nvm use --lts

python3 -m ensurepip --user 2>/dev/null || true
python3 -m pip install --user -q -r requirements.txt
python3 scripts/import_xlsm.py

npm install
npm run build

echo "Build complete. Run: npm run dev"
