import time
from typing import List
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import MerchantTransaction
from schemas import RiskEvaluationRequest, TransactionLedgerResponse
from risk_engine import evaluate_transaction_risk
from vector_store import fraud_vector_store

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PayPal Polyglot AI Risk & Dispute Microservice",
    description="PayPal Orders v2 & Disputes API + FAISS Vector Search + Gemini 2.5 Flash Adjudicator",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "python-paypal-ai-risk-engine"}

@app.post("/api/v1/risk/evaluate", response_model=TransactionLedgerResponse)
async def evaluate_risk(req: RiskEvaluationRequest, db: Session = Depends(get_db)):
    trace_id = req.gateway_trace_id or f"DIRECT-PY-{int(time.time() * 1000)}"
    eval_res = evaluate_transaction_risk(req)

    tx_record = MerchantTransaction(
        gateway_trace_id=trace_id,
        merchant_id=req.merchant_id,
        paypal_order_id=req.paypal_order_id or "PAYID-SBX-LOCAL",
        paypal_approve_url=req.paypal_approve_url,
        paypal_mode=req.paypal_mode or "PAYPAL_SANDBOX_EMULATOR",
        paypal_event_type=req.paypal_event_type or "CHECKOUT.ORDER.CREATED",
        amount_usd=req.amount_usd,
        velocity_1h=req.velocity_1h,
        cross_border=req.cross_border,
        historical_cb_rate=req.historical_cb_rate,
        dispute_claim=req.dispute_claim,
        risk_score=eval_res["risk_score"],
        decision=eval_res["decision"],
        dispute_win_prob=eval_res["dispute_win_prob"],
        faiss_nearest_distance=eval_res["faiss_nearest_distance"],
        matched_precedents=eval_res["matched_precedents"],
        llm_reasoning=eval_res["reasoning"],
        recommended_action=eval_res["recommended_action"],
        paypal_dispute_evidence=eval_res["paypal_dispute_evidence"],
        engine_mode=eval_res["engine_mode"]
    )
    db.add(tx_record)
    db.commit()
    db.refresh(tx_record)
    return tx_record

@app.get("/api/v1/risk/ledger", response_model=List[TransactionLedgerResponse])
async def get_recent_ledger(limit: int = 15, db: Session = Depends(get_db)):
    return (
        db.query(MerchantTransaction)
        .order_by(MerchantTransaction.id.desc())
        .limit(limit)
        .all()
    )

@app.get("/api/v1/risk/stats")
async def get_risk_stats(db: Session = Depends(get_db)):
    total_tx = db.query(MerchantTransaction).count()
    return {
        "ai_service_online": True,
        "faiss_indexed_vectors": fraud_vector_store.total_entries(),
        "vector_dimension": 4,
        "ledger_transactions_logged": total_tx
    }