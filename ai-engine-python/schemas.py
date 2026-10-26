from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RiskEvaluationRequest(BaseModel):
    merchant_id: str = Field(default="PAYPAL-MERCH-8841")
    amount_usd: float = Field(default=1450.0, gt=0)
    velocity_1h: int = Field(default=14, ge=1)
    cross_border: bool = Field(default=True)
    historical_cb_rate: float = Field(default=1.85, ge=0.0, le=100.0)
    dispute_claim: str = Field(
        default="PayPal Buyer opened UNAUTHORIZED_TRANSACTION claim on cross-border digital electronics order."
    )
    use_faiss: bool = Field(default=True)
    gateway_trace_id: Optional[str] = Field(default=None)
    paypal_order_id: Optional[str] = Field(default="PAYID-SBX-DEFAULT")
    paypal_approve_url: Optional[str] = Field(default="https://www.sandbox.paypal.com")
    paypal_mode: Optional[str] = Field(default="PAYPAL_SANDBOX_EMULATOR")
    paypal_event_type: Optional[str] = Field(default="CHECKOUT.ORDER.CREATED")

class LLMRiskOutput(BaseModel):
    risk_score: float = Field(description="Risk score from 0.0 (safe) to 100.0 (critical fraud)")
    decision: str = Field(description="One of: APPROVED, STEP_UP_3DS, BLOCKED_HOLD")
    dispute_win_prob: float = Field(description="Probability (0.0 to 1.0) merchant wins PayPal Seller Protection representment")
    reasoning: str = Field(description="Detailed PayPal Seller Protection & behavioral risk explanation")
    recommended_action: str = Field(description="Immediate PayPal Orders v2 / Disputes API action")

class TransactionLedgerResponse(BaseModel):
    id: int
    gateway_trace_id: str
    merchant_id: str
    paypal_order_id: str
    paypal_approve_url: Optional[str]
    paypal_mode: str
    paypal_event_type: str
    amount_usd: float
    velocity_1h: int
    cross_border: bool
    historical_cb_rate: float
    dispute_claim: Optional[str]
    risk_score: float
    decision: str
    dispute_win_prob: float
    faiss_nearest_distance: float
    matched_precedents: Optional[List[Dict[str, Any]]]
    llm_reasoning: str
    recommended_action: str
    paypal_dispute_evidence: Optional[Dict[str, Any]]
    engine_mode: str

    class Config:
        from_attributes = True