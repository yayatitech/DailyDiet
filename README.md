# DailyDiet — Weekly Meal Tracker

Static web app for the Fitelo weekly meal plan: **8 time slots × 7 days**, editable meals, and checkbox tracking saved in your browser.

**Project location (WSL):** `/home/pingmepls/projects/DailyDiet`

## Quick start (WSL)

Open a terminal in WSL (Ubuntu 24.04), then:

```bash
cd ~/projects/DailyDiet
export PATH="$HOME/.nvm/versions/node/v24.16.0/bin:/usr/bin:/bin:$PATH"
npm install
npm run dev
```

Open http://localhost:5173

### First-time WSL setup

If Node is not installed yet:

```bash
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.nvm/nvm.sh
nvm install --lts
```

Then run `npm install` and `npm run dev` as above.

## Re-import from Excel

When `simple_weekly_meal_plan_extendable.xlsm` changes:

```bash
python3 scripts/import_xlsm.py
```

Refresh the app (hard refresh if needed). This updates `public/data/meal-plan.json` only — not browser `localStorage`. Use **Reset week** in the app if a week still shows old/wrong meals.

## Data storage

| Location | What |
|----------|------|
| `public/data/meal-plan.json` | Seed plan from Excel |
| `localStorage` `dailyDiet.plan` | Your edited meals and notes |
| `localStorage` `dailyDiet.tracking` | Checkbox state |
| `localStorage` `dailyDiet.ui` | Last week / view preferences |

Use **Export JSON** to back up plan + tracking. **Import JSON** restores them.

## Build

```bash
npm run build
npm run preview
```

Output is in `dist/` for static hosting.

## Features

- Week grid: 8 meal time slots × Mon–Sun
- Day view for mobile
- Editable meals and week notes
- Checkbox tracking with strikethrough when done
- Today column highlight when week start date is set
