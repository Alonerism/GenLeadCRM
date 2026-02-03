# Campaign Backend (Orchestrator API)

This service is the **thin glue layer** that turns the three existing systems in this repo into a single campaign system:

- **Lead engine** (Python) → generates leads from filters
- **Voice agent** (Twilio/OpenAI) → executes calls
- **CRM frontend** (Vite React) → controls campaigns and views outcomes

It provides a stable REST API under `/api/*` (matching what `sunbeam-crm/src/lib/api.ts` already expects), plus webhook endpoints for Twilio + voice-agent telemetry.

## Run (local)

1. Create env:

```bash
cp env.example .env
```

2. Install and start:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Environment variables

- **CAMPAIGN_DB_PATH**: SQLite DB path (default: `./campaign.db`)
- **VOICE_AGENT_BASE_URL**: e.g. `https://your-voice-agent-host` (used for TwiML URL on outbound calls)
- **TWILIO_ACCOUNT_SID**, **TWILIO_AUTH_TOKEN**, **TWILIO_FROM_NUMBER**: enable outbound calls
- **GOOGLE_MAPS_API_KEY**: required by the lead engine

## Key endpoints

- Campaigns: `GET/POST /api/campaigns`, `PUT /api/campaigns/{id}/status`, `POST /api/campaigns/{id}/execute`
- Leads: `GET /api/campaigns/{id}/leads`, `PUT /api/leads/{id}`
- LeadGen: `POST /api/leadgen/run`, `GET /api/leadgen/runs`, `GET /api/leadgen/runs/{id}/results`, `POST /api/leadgen/runs/{id}/save-segment`
- Agents: `GET/PUT /api/agents/*`
- Webhooks: `POST /api/webhooks/twilio/call-status`, `POST /api/webhooks/voice-agent/tool-log`


