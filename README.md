# Census Assistant

An AI-powered field support system built for **Census 2027 operations in Lakhipur Circle, India**. It gives enumerators, supervisors, and administrators a single place to look up functionary records, search official census manuals, and get instant, citation-backed answers from an AI assistant — on the web, on an Android app, or over WhatsApp/Telegram.

![Android Build](https://github.com/Nukeio/Census-Assistant/actions/workflows/android-build.yml/badge.svg)

## Overview

Census Assistant pairs a Flask + SQLite backend with a lightweight vanilla-JS web app (also shipped as a native Android WebView wrapper) to solve a very concrete field problem: enumerators and supervisors need fast, accurate answers about their assignments and about census procedure, without waiting on a phone call to a technical assistant.

The backend ingests the official functionary allocation spreadsheets and PDF operating manuals into a searchable SQLite database, then answers questions two ways:

- **Structured lookups** — search by name, mobile number, HLB (House Listing Block) number, or supervisor, with results ranked by relevance.
- **Retrieval-augmented generation (RAG)** — natural-language questions are matched against indexed manual text and record data, then answered by an LLM (or a local synthesizer when no LLM key is configured) with the exact source cited.

## Key Features

- **Records Search** — look up any enumerator, supervisor, or field user by name, HLB block, or mobile number, with smart search-intent detection (a 3–4 digit query is treated as an HLB lookup, 5+ digits as a mobile number search) and name-relevance ranking.
- **Supervisor Directory** — browse supervisors with their assigned circles and the full list of enumerators reporting to them, including one-tap call/WhatsApp and map links.
- **AI Assistant** — ask questions in plain language (English, Assamese, Hindi, or Bengali) and get answers grounded strictly in the ingested census records and manuals, with a source citation on every response and a clear "not found" fallback rather than a guess.
- **Manual Search** — full-text search across the official Census FAQ and House Listing Operations (HLO) manuals.
- **Multi-channel access** — the same assistant is reachable through the web app, the Android app, and WhatsApp/Telegram (with a local web-chat and messenger fallback matrix), so field staff aren't limited to one channel.
- **Field Attendance** — enumerators and supervisors mark daily attendance from the app with their name, position, HLB/Supervisory Circle number, a camera photo and their live device location. One entry per person per day: resubmitting updates the existing entry rather than creating a duplicate. The admin reviews each entry, and approving it deletes the photo from the server permanently while keeping the record.
- **Role-aware access** — Guests get read-only access; OTP-verified field functionaries see personalized views; Admins get a full management console. Inactive/disabled accounts are automatically hidden from non-admin views.
- **Admin Console** — re-upload source Excel/PDF data, manage user status, review the attendance register and export it to Excel, inspect query logs and system health, and broadcast alerts/notices, all gated behind admin authentication.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite (with FTS5 full-text search) |
| AI / RAG | Google Gemini, OpenAI, or Anthropic (pluggable), with a built-in local RAG fallback that needs no API key |
| Frontend | Vanilla JavaScript SPA, Tailwind CSS (CDN), Material Symbols, Material Design 3–inspired UI |
| Mobile | Native Android WebView wrapper (Kotlin), built via GitHub Actions |
| Messaging | WhatsApp Business Cloud API, Telegram Bot API |
| Auth | JWT (guest / OTP-verified functionary / admin roles) |
| Deployment | Docker, Render (`render.yaml`), or any WSGI-capable host (e.g. PythonAnywhere) |

## Project Structure

```
Census-Assistant/
├── backend/              # Flask app, ingestion pipeline, RAG engine, auth, messaging
│   ├── main.py           # App entrypoint & all REST routes
│   ├── database.py       # Schema + connection helpers
│   ├── ingestion.py      # Excel/PDF → SQLite ingestion
│   ├── rag_engine.py     # Intent detection, structured + manual search
│   ├── llm_provider.py   # Multi-model AI adapter (Gemini/OpenAI/Anthropic/local)
│   ├── messaging_gateway.py  # WhatsApp/Telegram webhook handling
│   ├── attendance.py     # Daily field attendance register + Excel export
│   └── auth.py           # Guest, OTP, and admin authentication
├── frontend/             # Single-page web app (served by Flask, bundled into the APK)
├── android/              # Native Android WebView wrapper project
├── database/schema.sql   # Reference schema
├── tests/                # Backend test suite
├── Dockerfile, docker-compose.yml, render.yaml   # Deployment configs
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.11+
- (Optional) An API key for Gemini, OpenAI, or Anthropic — the app falls back to a local, non-LLM RAG synthesizer if none is set.

### Backend Setup

```bash
git clone https://github.com/Nukeio/Census-Assistant.git
cd Census-Assistant
python -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env              # then fill in the values you need
python -m backend.main
```

The app serves both the API and the frontend at `http://localhost:8080` (or whatever `PORT` you set). On first run it ingests the seed Excel/PDF data in the project root into a local `census_assistant.db`.

### Environment Variables

All configuration lives in `.env` (see `.env.example` for the full list). Nothing needs to be filled in to run locally — every integration degrades gracefully when its key is left blank:

| Variable | Purpose |
|---|---|
| `PORT` | Port the Flask server binds to |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | AI provider keys (optional — local synthesizer is used if all are empty) |
| `JWT_SECRET` | Signing key for auth tokens — **always set a strong, unique value in production** |
| `DEV_OTP_BYPASS` | Dev-only OTP shortcut — must stay `false` outside local development |
| `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN` | WhatsApp Business Cloud API integration |
| `TELEGRAM_BOT_TOKEN` | Telegram bot fallback channel |
| `TECH_ASSISTANT_NAME`, `TECH_ASSISTANT_PHONE`, `SUPERVISOR_NAME`, `CIRCLE_NAME` | Contact/branding details shown in the app and AI responses |

### Running with Docker

```bash
docker compose up --build
```

### Android App

See [`android/BUILD.md`](android/BUILD.md) for the full native build guide. The app is also built automatically on every push via [GitHub Actions](.github/workflows/android-build.yml); download the latest debug APK from the **Actions** tab.

### Deployment

- **Render**: connect the repo and Render will pick up `render.yaml` automatically.
- **Docker**: build and run the provided `Dockerfile` on any container host.
- **Traditional WSGI hosting** (e.g. PythonAnywhere): pull the repo, install `requirements.txt`, and point your WSGI config at `server:app`.

## Field Attendance

Field staff open **Attendance** from the home screen (or the side/drawer nav) and
submit five things: mobile number, full name, position (Enumerator or
Supervisor), HLB or Supervisory Circle number, a photo, and their live device
location. The mobile number is the identity key.

**One entry per person per day.** The `attendance_records` table is uniquely
constrained on `(mobile_number, attendance_date)` and the submit endpoint upserts
against it, so a person resubmitting on the same day always overwrites their own
entry — the register can never accumulate duplicate rows for the same person on
the same day. The attendance day is computed in IST regardless of server
timezone. Name, position and block number carry forward automatically from the
person's most recent entry, so a returning user only re-takes the photo and
re-confirms their location.

**Review workflow.** New and edited entries are `PENDING`. In the Admin Console's
*Field Attendance Register* the Technical Assistant can:

- **Approve** — the photo file is deleted from the server permanently and the
  entry is locked; the user can no longer edit it.
- **Reject** with a reason — the photo is kept and the user can correct and
  resubmit, which returns the entry to `PENDING`.

**Excel export.** *Export to Excel* downloads a single `.xlsx` containing every
matching entry — all users in one sheet, one row per person per day — honouring
whatever status, position, date-range and search filters are active. Photos are
never in the export; the Photo column just records whether the image is awaiting
review or was deleted on approval.

**Photos** live in `attendance_photos/` (git-ignored — this is personal data),
are only ever served to an authenticated admin, and are deleted on approval.
`POST /api/admin/attendance/purge-photos` clears any file no live record points
at.

**Location requires HTTPS.** Browsers and the Android WebView only expose
`navigator.geolocation` on a secure context, so deploy behind TLS for field use.
See [`android/ATTENDANCE_SETUP.md`](android/ATTENDANCE_SETUP.md) for the WebView
camera/geolocation wiring the Android app needs.

To verify the whole flow against a running server:

```bash
python -m backend.main                  # in one shell
python tests/test_attendance_flow.py    # in another
```

## Data & Privacy

This project ingests real census functionary data (names, mobile numbers, assignments) to function. That data is sensitive and should **never** be committed to a public repository. In production:

- Keep the deployment's environment and database private.
- Seed or refresh functionary/HLB data through the **Admin Console's** upload endpoints rather than committing spreadsheets to git.
- Treat `JWT_SECRET`, messaging API tokens, and any admin credentials as secrets — set them via environment variables only, never hardcoded.

## Roles & Access

| Role | Access |
|---|---|
| Guest | Read-only access to public records search, manuals, and the AI assistant |
| Field Functionary (OTP-verified) | Guest access plus a personalized view of their own assignment |
| Admin | Full console: data re-ingestion, user management, attendance review & Excel export, query logs, system health, alerts/notices |

## Contributing

Issues and pull requests are welcome. Please avoid including any real functionary data, credentials, or API keys in commits or issue reports.

## License

Released under the [MIT License](LICENSE).
