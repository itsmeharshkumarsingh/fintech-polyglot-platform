# Fintech Polyglot Platform: PayPal AI Risk & Dispute Gateway

A containerized, high-concurrency polyglot microservice architecture built for the **PayPal AI Hackathon**, combining a **Go (Gin) Edge Gateway** (integrated with **PayPal Sandbox Orders v2 & Webhooks APIs**) and an isolated **Python (FastAPI) AI & FAISS Vector Risk Engine** powered by **Gemini 2.5 Flash**.

## Polyglot Architecture & PayPal Integration

1. **Go (Gin) + PayPal Sandbox Edge Gateway (`/gateway-go`)**:
   - Exchanges OAuth 2.0 credentials against `https://api-m.sandbox.paypal.com/v1/oauth2/token`.
   - Creates live **PayPal Checkout Orders (`POST /v2/checkout/orders`)** and listens for **PayPal Dispute Webhooks (`POST /api/gateway/paypal/webhook`)**.
   - Enforces HS256 JWT authentication, atomic microsecond latency tracking, and real-time WebSocket event streaming (`/ws/telemetry`).
2. **Python (FastAPI) FAISS + Gemini 2.5 Flash Risk Engine (`/ai-engine-python`)**:
   - Encodes 4D transaction behavioral vectors into **FAISS (`IndexFlatL2`)** to retrieve nearest historical fraud/chargeback precedents.
   - Adjudicates transaction risk and compiles **PayPal Disputes API (`v1/customer/disputes/{id}/provide-evidence`)** representment packets automatically.
3. **Zero-Downtime Resilience**:
   - Includes automatic SQLAlchemy 2.0 cloud URI healing, PayPal Sandbox emulation fallback, and a Bayesian log-odds fallback scorer.

## Quickstart (Docker Compose)

```bash
cp .env.example .env
# Add your PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, and GEMINI_API_KEY inside .env
docker-compose up --build -d