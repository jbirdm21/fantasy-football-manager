# Ultimate Personal Fantasy Football Manager (UPFFM)

A comprehensive fantasy football management system for dominating ESPN and Yahoo leagues.

## Features

- **Draft-day war-room:** Tiers, value-based drafting, pick simulations, real-time league sync
- **Roster optimization:** Weekly start/sit, FAAB/waiver recommendations, rest-of-season value
- **Trade machine:** Fair-value engine, injury/suspension risk, schedule strength
- **In-game coach:** Live win-probability models, tilt-proof swap alerts
- **Explainability:** Surface the stats & math that drove each recommendation

## Project Structure

```
fantasy-football-manager/
├── backend/          # FastAPI application
├── frontend/         # Next.js frontend
├── data/             # Data processing scripts and pipelines
├── docs/             # Project documentation and diagrams
└── tests/            # Test suites
```

## Development Timeline

- **Target MVP:** September 2025 (in time for fantasy drafts)
- **Initial Development:** April-August 2025

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, uvicorn
- **Database:** PostgreSQL with Timescale extension, DuckDB/Polars
- **Frontend:** Next.js (React 18), shadcn/ui
- **Data Pipeline:** Dagster or Prefect
- **Testing:** pytest with 95%+ coverage
- **Deployment:** Docker, GitHub Actions 