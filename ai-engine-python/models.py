from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, Text
from database import Base

class MerchantTransaction(Base):
    __tablename__ = "merchant_transactions"

    id = Column(Integer, primary_key=True, index=True)
    gateway_trace_id = Column(String(64), unique=True, index=True, nullable=False)
    merchant_id = Column(String(64), index=True, nullable=False)

    # PayPal Sandbox Order & Webhook Metadata
    paypal_order_id = Column(String(64), index=True, nullable=False)
    paypal_approve_url = Column(String(256), nullable=True)
    paypal_mode = Column(String(64), nullable=False)
    paypal_event_type = Column(String(64), nullable=False)

    # Telemetry & Behavioral Features
    amount_usd = Column(Float, nullable=False)
    velocity_1h = Column(Integer, nullable=False)
    cross_border = Column(Boolean, default=False)
    historical_cb_rate = Column(Float, nullable=False)
    dispute_claim = Column(Text, nullable=True)

    # FAISS + AI Risk Outputs
    risk_score = Column(Float, nullable=False)
    decision = Column(String(32), index=True, nullable=False)  # APPROVED, STEP_UP_3DS, BLOCKED_HOLD
    dispute_win_prob = Column(Float, nullable=False)
    faiss_nearest_distance = Column(Float, nullable=False)
    matched_precedents = Column(JSON, nullable=True)
    llm_reasoning = Column(Text, nullable=False)
    recommended_action = Column(String(256), nullable=False)
    paypal_dispute_evidence = Column(JSON, nullable=True)
    engine_mode = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)