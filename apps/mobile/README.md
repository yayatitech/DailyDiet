# DailyDiet Mobile (Expo)

Phase 3 scaffold for the DailyDiet API.

## Setup

```bash
cd apps/mobile
npm install
```

Set API URL (device/emulator must reach your machine):

```bash
export EXPO_PUBLIC_API_URL=http://YOUR_LAN_IP:3000
npm start
```

## Next steps

- Week detail + day view screens
- JWT auth (reuse tokens from web)
- Completion toggles synced via `/v1/weeks/{id}/completions`

See [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
