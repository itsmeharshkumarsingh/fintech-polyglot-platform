# PayPal Merchant AI Gateway & Dispute Adjudicator | Polyglot Platform

#### 🔗 [Live Deployment Link](https://fintech-frontend.onrender.com)

A high-performance, polyglot microservice architecture designed to automate merchant risk scoring, sandbox transaction processing, and dispute adjudication using real-time AI and vector memory.

This project provides a technical deep-dive into combining **Go (Gin) for high-concurrency edge routing**, **Python (FastAPI + Gemini AI)** for intelligent risk analysis, **FAISS for vector similarity search**, and **PostgreSQL** for immutable transactional ledgers.

## About The Project

This project simulates a modern fintech infrastructure where automated real-time fraud detection and instantaneous dispute handling are critical for merchant survival:

> **The Problem:** Traditional e-commerce and payment gateways process millions of transactions with static rule-based fraud filters, leading to high false-positive rates and slow manual dispute resolutions. Furthermore, historical dispute patterns are rarely indexed for fast semantic retrieval.

PayPal Merchant AI Gateway solves this by decoupling edge routing from heavy AI computation, leveraging vector memory to match live transactions against historical fraud precedents instantly.

## Features

*   **Go Edge Gateway & JWT Security:** High-concurrency routing layer managing secure `HS256` JWT sessions and merchant cluster telemetry.
*   **AI-Powered Risk Engine:** Integrates **Google Gemini 2.5 Flash** and **FAISS (Facebook AI Similarity Search)** to analyze dispute precedents and compute intelligent risk scores.
*   **PayPal Sandbox Integration:** End-to-end simulation supporting PayPal Orders v2 REST API and automated webhook triggers (`CUSTOMER.DISPUTE.CREATED`).
*   **Immutable PostgreSQL Ledger:** Secure relational logging tracking every routed order, risk verdict, and adjudication outcome.
*   **Streamlit Interactive Dashboard:** Real-time visual monitoring of goroutines, FAISS memory state, and active telemetry.

## The Engineering Logic Explained

### 1. The Challenge: High-Throughput vs. Heavy AI Computation
Handling high-volume API requests while running complex Large Language Model (LLM) prompts creates unacceptable latency bottlenecks if handled in a monolithic application layer.

### 2. The Solution: Polyglot Microservice Separation
We implement a distributed polyglot design:
1.  **The Edge (Go/Gin):** Acts as the ultra-fast API gateway, handling token generation, request validation, and proxying with minimal CPU overhead.
2.  **The Intelligence Layer (Python/FastAPI):** Handles heavy AI processing, prompt engineering, and vector database queries asynchronously.
3.  **The Data Layer (PostgreSQL):** Guarantees relational durability and transactional tracking across microservices.

### 3. Vector Similarity & Precedent Matching
By embedding historical dispute data into a **FAISS vector store**, the system performs sub-millisecond nearest-neighbor searches to feed relevant contextual precedents directly into the Gemini risk model during adjudication.

## Getting Started

To get a local copy of this polyglot architecture running via Docker Compose, follow these steps:

1.  **Clone the repo:**
    ```sh
    git clone [https://github.com/itsmeharshkumarsingh/fintech-polyglot-platform.git](https://github.com/itsmeharshkumarsingh/fintech-polyglot-platform.git)
    ```
2.  **Navigate to the directory:**
    ```sh
    cd fintech-polyglot-platform
    ```
3.  **Configure Environment:** Create a `.env` file in the root directory and add your credentials:
    ```env
    DATABASE_URL=postgresql://user:password@localhost:5432/fintech_polyglot_db
    GEMINI_API_KEY=your_gemini_api_key_here
    PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
    PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
    ```
4.  **Launch with Docker Compose:**
    ```sh
    docker-compose up --build
    ```

## Technology Stack

*   **Go (Gin):** For asynchronous, high-concurrency API edge routing and token management.
*   **Python (FastAPI):** For machine learning orchestration, risk evaluation, and vector retrieval.
*   **PostgreSQL:** For relational data persistence and immutable transaction logging.
*   **Streamlit:** For building the interactive front-end analytics dashboard.
*   **FAISS & Google Gemini:** For vector similarity indexing and advanced LLM risk inference.

## Demo

![gif of the Fintech Platform Demo](demo.gif)

---

## Contributing

As this project was built for the PayPal AI Hackathon, external contributions are currently closed. However, architectural feedback, ideas, and suggestions are always welcome!

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/Optimization`)
3.  Commit your Changes (`git commit -m 'Optimized Go router concurrency'`)
4.  Push to the Branch (`git push origin feature/Optimization`)
5.  Open a Pull Request