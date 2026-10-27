<div align="center">

# PayPal Merchant AI Gateway & Dispute Adjudicator

### Enterprise-grade **polyglot fintech infrastructure**: Go Edge Gateway + Agentic AI Risk Scoring + FAISS Vector Memory + Immutable Ledger

[![Live Demo](https://img.shields.io/badge/Live_Deployment-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://fintech-frontend-l3fm.onrender.com/)
[![Go](https://img.shields.io/badge/Go-1.22+-00ADD8?logo=go&logoColor=white)](https://go.dev/)
[![Gin](https://img.shields.io/badge/Gin-Edge_Gateway-008ECF?logo=go&logoColor=white)](https://gin-gonic.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini_2.5_Flash-8E75B2?logo=googlegemini&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-0467DF?logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss)
[![PayPal](https://img.shields.io/badge/PayPal_Orders_v2-00457C?logo=paypal&logoColor=white)](https://developer.paypal.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Merchant Order / Webhook -> Go Edge Gateway (HS256 JWT) -> FastAPI + FAISS Vector Search -> Gemini 2.5 Adjudicator -> Immutable PostgreSQL Ledger**

<h4>
  <a href="https://fintech-frontend-l3fm.onrender.com/">View Live Deployment</a>
  <span> · </span>
  <a href="#quick-start-local">Quick Start</a>
  <span> · </span>
  <a href="#architecture">Architecture</a>
</h4>

</div>

---

A high-performance, **polyglot microservice platform** engineered for the **PayPal AI Hackathon** to automate merchant risk scoring, sandbox checkout processing, and real-time dispute adjudication. It decouples ultra-low-latency **Go (Gin) edge routing** from asynchronous **Python (FastAPI + Google Gemini 2.5 Flash)** intelligence, leveraging **FAISS vector similarity search** over historical fraud precedents and an **immutable PostgreSQL transactional ledger**.

## Table of Contents
1. [The Engineering Problem & Solution](#the-engineering-problem--solution)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Request & Webhook Lifecycle](#request--webhook-lifecycle)
5. [Tech Stack](#tech-stack)
6. [Project Structure](#project-structure)
7. [Quick Start (Local)](#quick-start-local)
8. [Key API Endpoints](#key-api-endpoints)
9. [Vector Memory & Precedent Adjudication](#vector-memory--precedent-adjudication)
10. [Environment Variables](#environment-variables)
11. [Roadmap](#roadmap)
12. [Troubleshooting](#troubleshooting)
13. [Contributing & License](#contributing--license)

---

## The Engineering Problem & Solution

> **The Problem:** Traditional payment gateways evaluate millions of transactions using rigid, static rule-based fraud filters—leading to high false-positive declines on legitimate buyers and slow, manual chargeback dispute resolution. Meanwhile, running heavy Large Language Model (LLM) inference directly inside a monolithic API layer introduces severe latency bottlenecks under high concurrency.

**The Polyglot Solution:**
1. **The Edge Layer (`Go / Gin`):** Acts as a high-concurrency ingress gateway managing `HS256` JWT validation, rate limiting, PayPal webhook ingestion, and goroutine telemetry with minimal CPU/memory overhead.
2. **The Intelligence Layer (`Python / FastAPI`):** Offloads compute-intensive embeddings, sub-millisecond **FAISS** nearest-neighbor searches, and **Gemini 2.5 Flash** risk reasoning into an asynchronous microservice.
3. **The Ledger Layer (`PostgreSQL`):** Guarantees ACID-compliant relational durability and append-only audit trails across every routed transaction, risk verdict, and dispute outcome.

---

## Features

| Feature | Description |
|---|---|
| **Go Edge Gateway** | High-concurrency `Gin` reverse proxy & router handling `HS256` JWT session security and live cluster telemetry |
| **AI Risk Engine** | Real-time transaction risk scoring powered by **Google Gemini 2.5 Flash** and structured prompt reasoning |
| **FAISS Vector Memory** | Sub-millisecond semantic similarity search matching live disputes against indexed historical fraud precedents |
| **PayPal Sandbox v2** | End-to-end integration with **PayPal Orders v2 REST API** and automated `CUSTOMER.DISPUTE.CREATED` webhooks |
| **Auto-Adjudicator** | Synthesizes transaction metadata, buyer history, and top-$k$ FAISS precedents to issue instant dispute verdicts |
| **Immutable Ledger** | Append-only PostgreSQL schema recording every order state transition, risk score, and adjudication trace |
| **Streamlit Telemetry** | Interactive real-time operator dashboard monitoring active goroutines, FAISS index state, and ledger metrics |
| **Containerized Infra** | Multi-service `docker-compose` orchestration isolating Go edge, Python AI, PostgreSQL, and Streamlit |

---

## Architecture

```mermaid
flowchart TD
    M[Merchant / Buyer] --> GW["Go Gin Edge Gateway<br/>HS256 JWT Auth<br/>Telemetry & Proxy"]
    PP["PayPal Sandbox API<br/>Orders v2 & Webhooks"] <--> GW

    GW -- High-Concurrency RPC/HTTP --> AI["FastAPI Intelligence Service<br/>Async Risk & Dispute Engine"]

    AI --> EMB["Embedding Pipeline<br/>Vector Encoding"]
    EMB <--> FAISS[("FAISS Vector Store<br/>Historical Fraud Precedents")]

    AI <--> GEM["Google Gemini 2.5 Flash<br/>Risk Scoring & Adjudication"]

    GW -.-> PG[("PostgreSQL 16<br/>Immutable Transaction Ledger")]
    AI -.-> PG

    ST["Streamlit Dashboard (UI)<br/>Live Goroutine Telemetry & Audit Log"] --> GW
    ST -.-> PG
```

<details>
<summary>ASCII version</summary>

```text
          ┌──────────────────────────────────────────────────────────┐
          │            Streamlit Operator Dashboard (UI)             │
          │    Live Goroutine Telemetry · FAISS State · Audit Log    │
          └────────────────────────────┬─────────────────────────────┘
                                       │
          ┌────────────────────────────▼─────────────────────────────┐
          │               Go (Gin) Edge API Gateway                  │
          │   HS256 JWT Auth · PayPal Webhooks · Concurrency Router  │
          └──────┬─────────────────────┬──────────────────────┬──────┘
                 │                     │                      │
      PayPal Orders v2 REST    Async Proxy Route       Immutable Writes
                 │                     │                      │
          ┌──────▼──────┐   ┌──────────▼───────────┐   ┌──────▼──────┐
          │   PayPal    │   │   FastAPI Risk &     │   │ PostgreSQL  │
          │   Sandbox   │   │  Adjudication Engine │   │   Ledger    │
          │  Webhooks   │   │  (Python 3.11 Async) │   │ (ACID DB)   │
          └─────────────┘   └────┬─────────────┬───┘   └─────────────┘
                                 │             │
                        Top-K Precedents   LLM Inference
                                 │             │
                          ┌──────▼──────┐ ┌────▼───────────┐
                          │    FAISS    │ │ Google Gemini  │
                          │ Vector Store│ │   2.5 Flash    │
                          └─────────────┘ └────────────────┘
```
</details>

---

## Request & Webhook Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor C as Client / PayPal Webhook
    participant G as Go Edge Gateway (Gin)
    participant P as PayPal Sandbox v2
    participant F as FastAPI Risk Engine
    participant V as FAISS Vector Memory
    participant L as Gemini 2.5 Flash
    participant D as PostgreSQL Ledger

    C->>G: POST /api/v1/orders or Webhook (HS256 JWT)
    G->>G: Validate JWT & update goroutine telemetry
    G->>F: Forward transaction / dispute payload
    F->>V: Embed payload & query top-k similar historical disputes
    V-->>F: Return nearest-neighbor fraud precedents + distances
    F->>L: Prompt Gemini 2.5 Flash with payload + FAISS precedents
    L-->>F: Return {risk_score, verdict, reasoning, confidence}
    alt Verdict == APPROVE
        G->>P: Execute PayPal Orders v2 Capture
        P-->>G: Order Capture Confirmed
    else Verdict == FLAG / ADJUDICATE DISPUTE
        F->>D: Log automated dispute evidence & adjudication decision
    end
    G->>D: Append immutable audit record (order_id, score, trace)
    G-->>C: JSON Response {status, risk_score, verdict, ledger_tx_id}
```

<details>
<summary>Text version</summary>

```text
Client / PayPal Webhook -> POST /api/v1/orders (or /webhooks/dispute)
  │
  ├─ 1. Go Edge Gateway (Gin): Validates HS256 JWT & records active goroutine metrics
  ├─ 2. Proxies structured payload to FastAPI Intelligence Layer
  ├─ 3. FastAPI Risk Engine:
  │      ├─ Encodes transaction/dispute context into dense vector embeddings
  │      ├─ Queries FAISS index for top-k historical dispute precedents
  │      ├─ Passes live context + retrieved precedents to Google Gemini 2.5 Flash
  │      └─ Computes structured Risk Verdict {score, decision, explanation}
  ├─ 4. PayPal Sandbox Integration: Captures order or processes CUSTOMER.DISPUTE.CREATED
  ├─ 5. Persists append-only audit entry into PostgreSQL Immutable Ledger
  └─ 6. Returns real-time JSON adjudication verdict to Merchant / Streamlit UI
```
</details>

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Edge API Gateway** | Go (Golang), Gin Web Framework, `golang-jwt` (`HS256`), Goroutine Telemetry |
| **AI & Risk Service** | Python 3.11, FastAPI, Uvicorn, Pydantic v2 |
| **LLM Reasoning** | Google Gemini 2.5 Flash (`google-generativeai`) |
| **Vector Memory** | FAISS (Facebook AI Similarity Search) — sub-millisecond L2/Cosine indexing |
| **Payment Rail** | PayPal REST API (Orders v2, Sandbox Webhooks, `CUSTOMER.DISPUTE.CREATED`) |
| **Transactional Ledger** | PostgreSQL 16 (Immutable audit schema, relational transaction logging) |
| **Frontend & Telemetry** | Streamlit (Real-time cluster monitor, FAISS inspector, interactive sandbox) |
| **Infrastructure** | Docker, Docker Compose, Render Cloud Deployment |

---

## Project Structure

```text
fintech-polyglot-platform/
├── .vscode/
│   └── settings.json
├── ai-engine-python/             # Python (FastAPI) AI Risk & Adjudication Engine
│   ├── database.py             # PostgreSQL connection & ledger session
│   ├── Dockerfile
│   ├── main.py                 # FastAPI app entry point & router mounting
│   ├── models.py               # Immutable ledger ORM / data models
│   ├── requirements.txt
│   ├── risk_engine.py          # Gemini 2.5 Flash risk scoring logic
│   ├── schemas.py              # Pydantic v2 request/response validation
│   └── vector_store.py         # FAISS index manager & precedent retrieval
├── frontend/                   # Streamlit Telemetry & Operator UI
│   ├── .streamlit/
│   │   └── config.toml
│   ├── app.py                  # Operator dashboard, telemetry & simulator
│   ├── Dockerfile
│   └── requirements.txt
├── gateway_go/                 # Go High-Concurrency Edge Gateway
│   ├── Dockerfile
│   ├── go.mod
│   └── main.go                 # Gin router, JWT middleware, proxy & telemetry
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml          # Full polyglot stack orchestration
├── LICENSE
└── README.md
```

---

## Quick Start (Local)

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone [https://github.com/itsmeharshkumarsingh/fintech-polyglot-platform.git](https://github.com/itsmeharshkumarsingh/fintech-polyglot-platform.git)
cd fintech-polyglot-platform

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and PayPal Sandbox credentials

# 3. Build and launch the polyglot stack
docker-compose up --build
```

| Service | Local URL | Description |
|---|---|---|
| **Streamlit Dashboard** | `http://localhost:8501` | Interactive UI, telemetry & dispute simulator |
| **Go Edge Gateway** | `http://localhost:8080` | High-concurrency ingress & JWT router |
| **FastAPI Risk Engine** | `http://localhost:8000/docs` | Swagger UI for AI risk & FAISS endpoints |
| **PostgreSQL Ledger** | `localhost:5432` | Relational immutable ledger database |

### Option B: Manual Service Execution

```bash
# 1. Start FastAPI Intelligence Layer
cd intelligence-py
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Start Go Edge Gateway (in a new terminal)
cd gateway-go
go mod download
go run cmd/main.go

# 3. Launch Streamlit Dashboard (in a new terminal)
cd dashboard-streamlit
streamlit run app.py
```

---

## Key API Endpoints

| Service | Method | Path | Description |
|---|---|---|---|
| **Go Edge** | `POST` | `/api/v1/auth/token` | Issue `HS256` signed merchant JWT session |
| **Go Edge** | `POST` | `/api/v1/orders/create` | Create & risk-screen a PayPal Sandbox v2 order |
| **Go Edge** | `POST` | `/api/v1/webhooks/paypal` | Ingest `CUSTOMER.DISPUTE.CREATED` webhook events |
| **Go Edge** | `GET` | `/api/v1/telemetry` | Fetch active Go goroutines, memory & latency stats |
| **FastAPI** | `POST` | `/api/v1/risk/evaluate` | Compute Gemini 2.5 risk score + FAISS precedent match |
| **FastAPI** | `POST` | `/api/v1/disputes/adjudicate` | Automated dispute resolution with vector evidence |
| **FastAPI** | `GET` | `/api/v1/faiss/status` | Inspect indexed vector count & precedent clusters |
| **Ledger** | `GET` | `/api/v1/ledger/audit` | Query immutable PostgreSQL transaction & verdict logs |

---

## Vector Memory & Precedent Adjudication

Instead of relying on static `if/else` velocity rules, every transaction and dispute passes through a **3-stage cognitive pipeline**:

| Stage | Mechanism | Engineering Impact |
|---|---|---|
| **1. Vector Indexing** | Historical chargebacks & fraud patterns are embedded into **FAISS** | Enables sub-millisecond $L_2$ similarity lookup across prior merchant disputes |
| **2. Context Augmentation** | Top-$k$ nearest historical precedents are retrieved per live request | Grounds the LLM in real empirical fraud data rather than zero-shot guessing |
| **3. Gemini 2.5 Flash Verdict** | Structured JSON evaluation synthesizes live metadata + precedents | Outputs deterministic `risk_score ∈ [0.0, 1.0]`, action verdict, and audit trail |

---

## Environment Variables

Create a `.env` file in the root directory before launching:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql://user:password@localhost:5432/fintech_polyglot_db`) |
| `GEMINI_API_KEY` | Google Gemini API key for Gemini 2.5 Flash risk inference |
| `PAYPAL_CLIENT_ID` | PayPal Developer Sandbox Client ID |
| `PAYPAL_CLIENT_SECRET` | PayPal Developer Sandbox Client Secret |
| `JWT_SECRET` | Secret key used by the Go Edge Gateway to sign/verify `HS256` tokens |

---

## Roadmap

- [x] High-concurrency Go (Gin) edge gateway with `HS256` JWT middleware
- [x] Asynchronous FastAPI + Gemini 2.5 Flash risk scoring engine
- [x] In-memory FAISS vector store for sub-millisecond dispute precedent matching
- [x] PayPal Orders v2 Sandbox & `CUSTOMER.DISPUTE.CREATED` webhook automation
- [ ] gRPC + Protocol Buffers between Go Edge and Python Intelligence layer
- [ ] Kubernetes Helm charts with Horizontal Pod Autoscaling (HPA)
- [ ] Prometheus & Grafana distributed tracing (OpenTelemetry)

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `401 Unauthorized` at Go Gateway | Ensure a valid `Bearer <JWT>` token is passed in the `Authorization` header |
| Gemini inference timeout or error | Verify `GEMINI_API_KEY` is valid and has quota for `gemini-2.5-flash` |
| PayPal Order creation fails | Confirm `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` belong to an active Sandbox app |
| Database connection refused | Ensure PostgreSQL container is healthy (`docker ps`) and `DATABASE_URL` matches port `5432` |

---

## Contributing & License

Developed originally for the **PayPal AI Hackathon**. While external pull requests are currently paused during judging, architectural feedback and issue reports are always welcome:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/Optimization`)
3. Commit your changes (`git commit -m 'Optimize Go router concurrency'`)
4. Push to the branch (`git push origin feature/Optimization`)
5. Open a Pull Request

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

<div align="center">

### If you find this polyglot architecture useful, give the repository a star.

</div>