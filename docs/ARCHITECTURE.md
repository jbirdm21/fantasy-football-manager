# UPFFM Architecture

This document outlines the high-level architecture of the Ultimate Personal Fantasy Football Manager application.

## System Overview

```mermaid
graph TD
    User[User] --> Frontend[Next.js Frontend]
    Frontend --> API[FastAPI Backend]
    
    %% Data Sources
    API --> ESPN[ESPN Fantasy API]
    API --> Yahoo[Yahoo Fantasy API]
    API --> Sleeper[Sleeper API]
    API --> FP[FantasyPros]
    API --> PFR[Pro Football Reference]
    API --> nflfastR[nflfastR Data]
    
    %% Backend Components
    API --> DB[(PostgreSQL)]
    API --> Analytics[Data Science Layer]
    API --> ETL[ETL Pipeline]
    
    %% Analytics Components
    Analytics --> Projections[Player Projections]
    Analytics --> Draft[Draft Analyzer]
    Analytics --> Roster[Roster Optimizer]
    Analytics --> Trade[Trade Calculator]
    Analytics --> Live[Live Game Analysis]
    
    %% ETL Details
    ETL --> Dagster[Dagster]
    Dagster --> DB
    
    %% DB Extensions
    DB --> TimescaleDB[TimescaleDB Extension]
    DB --> DuckDB[DuckDB Analytics]
    
    class User,Frontend,API,ESPN,Yahoo,Sleeper,FP,PFR,nflfastR,DB,Analytics,ETL,Projections,Draft,Roster,Trade,Live,Dagster,TimescaleDB,DuckDB user
```

## Component Details

### Frontend

- **Technology**: Next.js (React 18)
- **UI Components**: shadcn/ui
- **State Management**: React Context and SWR for data fetching
- **Features**:
  - Responsive design
  - Dark mode support
  - PWA capabilities for mobile use

### Backend API

- **Technology**: FastAPI on Python 3.11+
- **Authentication**: JWT-based authentication
- **Key Endpoints**:
  - League management
  - Player data
  - Projections
  - Draft tools
  - Roster optimization
  - Trade analysis

### Data Storage

- **Primary Database**: PostgreSQL with TimescaleDB extension
- **Analytics Engine**: DuckDB/Polars for high-performance queries
- **Key Tables**:
  - Players
  - Teams
  - Leagues
  - Projections
  - Historical stats
  - Draft data

### ETL Pipeline

- **Orchestration**: Dagster
- **Data Sources**:
  - ESPN Fantasy API
  - Yahoo Fantasy API
  - Sleeper API
  - FantasyPros
  - Pro Football Reference
  - nflfastR data
- **Schedules**:
  - Daily player updates
  - Hourly league syncs during game days
  - Weekly projection updates

### Analytics Layer

- **Libraries**: pandas/Polars, scikit-learn, XGBoost, LightGBM
- **Key Models**:
  - Player projections
  - Value-based drafting metrics
  - Lineup optimization
  - Trade fairness evaluation
  - Win probability predictions

## Deployment Architecture

The application is deployed as a set of Docker containers, making it easy to run locally or deploy to a cloud environment.

```mermaid
graph TD
    Docker[Docker Compose] --> Backend[Backend Container]
    Docker --> Frontend[Frontend Container]
    Docker --> DB[PostgreSQL Container]
    Docker --> ETL[Dagster Container]
    
    Backend --> DB
    Frontend --> Backend
    ETL --> DB
    ETL --> Backend
    
    class Docker,Backend,Frontend,DB,ETL deployment
``` 