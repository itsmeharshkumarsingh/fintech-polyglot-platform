import os
import re
import math
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from schemas import RiskEvaluationRequest, LLMRiskOutput
from vector_store import encode_tx_vector, fraud_vector_store

RISK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an autonomous PayPal Risk, Checkout & Dispute Adjudication Engine. "
        "Analyze the incoming PayPal Sandbox Order telemetry, merchant chargeback baseline, "
        "and FAISS nearest-neighbor historical precedents to compute a fraud score and "
        "PayPal Seller Protection representment strategy.\n\n"
        "Respond strictly with a single JSON block matching this schema:\n"
        "```json\n"
        '{{\n'
        '  "risk_score": 78.5,\n'
        '  "decision": "STEP_UP_3DS",\n'
        '  "dispute_win_prob": 0.64,\n'
        '  "reasoning": "Detailed quantitative synthesis of velocity, cross-border exposure, and FAISS matches.",\n'
        '  "recommended_action": "Hold PayPal Order v2 capture; require PAYER_ACTION 3DS2 challenge and log proof-of-delivery."\n'
        '}}\n'
        "```"
    )),
    ("human", (
        "--- PAYPAL ORDER & TELEMETRY ---\n"
        "PayPal Order ID: {paypal_order_id} ({paypal_event_type})\n"
        "Merchant ID: {merchant_id}\n"
        "Amount (USD): ${amount_usd:.2f}\n"
        "1-Hour Tx Velocity: {velocity_1h} tx/hr\n"
        "Cross-Border Routing: {cross_border}\n"
        "Merchant Historical Chargeback Rate: {historical_cb_rate:.2f}%\n"
        "Dispute / Checkout Context: {dispute_claim}\n\n"
        "--- FAISS VECTOR NEAREST PRECEDENTS ---\n"
        "{faiss_context}\n"
    ))
])

def build_paypal_dispute_evidence(
    req: RiskEvaluationRequest,
    eval_data: Dict[str, Any],
    precedents: List[Dict[str, Any]],
    nearest_dist: float
) -> Dict[str, Any]:
    """Builds a PayPal Disputes API (v1/customer/disputes/{id}/provide-evidence) compliant payload."""
    return {
        "paypal_dispute_api_schema": "v1/customer/disputes/provide-evidence",
        "paypal_order_id": req.paypal_order_id,
        "paypal_event_trigger": req.paypal_event_type,
        "evidence_type": "PROOF_OF_FULFILLMENT_AND_BEHAVIORAL_TELEMETRY",
        "seller_protection_eligibility": "ELIGIBLE" if eval_data["risk_score"] < 70 else "HIGH_RISK_HOLD",
        "adjudication_summary": {
            "decision": eval_data["decision"],
            "composite_risk_score": eval_data["risk_score"],
            "estimated_representment_win_prob": eval_data["dispute_win_prob"],
            "faiss_l2_nearest_distance": nearest_dist,
            "closest_historical_cluster": precedents[0]["label"] if precedents else "NONE"
        },
        "notes": eval_data["reasoning"],
        "recommended_gateway_hook": eval_data["recommended_action"]
    }

def statistical_fallback_scoring(
    req: RiskEvaluationRequest,
    precedents: List[Dict[str, Any]],
    nearest_dist: float
) -> Dict[str, Any]:
    """Deterministic Bayesian log-odds + FAISS k-NN weighted risk scorer when LLM quota is unavailable."""
    amt_factor = min(math.log10(max(req.amount_usd, 1.0) + 1.0) * 14.5, 45.0)
    vel_factor = min(req.velocity_1h * 1.65, 30.0)
    xb_factor = 14.0 if req.cross_border else 0.0
    cb_factor = min(req.historical_cb_rate * 8.5, 25.0)
    heuristic_score = min(max(amt_factor + vel_factor + xb_factor + cb_factor - 12.0, 2.0), 99.0)

    if precedents:
        knn_avg = sum(p["historical_score"] for p in precedents) / len(precedents)
        final_score = round(0.55 * heuristic_score + 0.45 * knn_avg, 2)
    else:
        final_score = round(heuristic_score, 2)

    if final_score >= 75.0:
        decision = "BLOCKED_HOLD"
        win_prob = round(max(0.18, 1.0 - (final_score / 115.0)), 2)
        action = (
            f"Block PayPal Order {req.paypal_order_id} capture; auto-compile PayPal Disputes API "
            "PROOF_OF_FULFILLMENT packet and freeze payout."
        )
    elif final_score >= 42.0:
        decision = "STEP_UP_3DS"
        win_prob = round(0.68 - (final_score - 42.0) * 0.006, 2)
        action = (
            f"Place PayPal Order {req.paypal_order_id} in PAYER_ACTION_REQUIRED state; "
            "enforce 3DSecure 2.2 step-up challenge."
        )
    else:
        decision = "APPROVED"
        win_prob = round(min(0.94, 0.78 + (42.0 - final_score) * 0.004), 2)
        action = (
            f"Execute immediate POST /v2/checkout/orders/{req.paypal_order_id}/capture "
            "under PayPal Seller Protection."
        )

    top_label = precedents[0]["label"] if precedents else "BASELINE_PROFILE"
    reasoning = (
        f"PayPal Order {req.paypal_order_id} ({req.paypal_event_type}) evaluated via multi-variate log-odds "
        f"(${req.amount_usd:,.2f}, velocity={req.velocity_1h} tx/hr, cross_border={req.cross_border}, "
        f"CB baseline={req.historical_cb_rate:.2f}%). FAISS L2 nearest-neighbor search (d={nearest_dist:.4f}) "
        f"matched precedent '{top_label}', yielding a composite risk index of {final_score}/100 ({decision})."
    )
    return {
        "risk_score": final_score,
        "decision": decision,
        "dispute_win_prob": win_prob,
        "reasoning": reasoning,
        "recommended_action": action,
        "engine_mode": "FAISS_BAYESIAN_FALLBACK"
    }

def evaluate_transaction_risk(req: RiskEvaluationRequest) -> Dict[str, Any]:
    tx_vec = encode_tx_vector(req.amount_usd, req.velocity_1h, req.cross_border, req.historical_cb_rate)
    nearest_dist, precedents = (0.0, [])
    if req.use_faiss:
        nearest_dist, precedents = fraud_vector_store.search_precedents(tx_vec, k=3)

    faiss_str = "\n".join([
        f"- [{p['label']}] Score: {p['historical_score']}/100 (L2 Dist: {p['l2_distance']}): {p['summary']}"
        for p in precedents
    ]) if precedents else "No prior FAISS vectors queried."

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    valid_key = bool(api_key and api_key != "your_actual_gemini_api_key_here")

    result_data = None
    if valid_key:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
            parser = PydanticOutputParser(pydantic_object=LLMRiskOutput)
            chain = RISK_PROMPT | llm
            resp = chain.invoke({
                "paypal_order_id": req.paypal_order_id,
                "paypal_event_type": req.paypal_event_type,
                "merchant_id": req.merchant_id,
                "amount_usd": req.amount_usd,
                "velocity_1h": req.velocity_1h,
                "cross_border": req.cross_border,
                "historical_cb_rate": req.historical_cb_rate,
                "dispute_claim": req.dispute_claim,
                "faiss_context": faiss_str
            })
            j_match = re.search(r"```(?:json)?\s*(.*?)\s*```", resp.content, re.DOTALL)
            raw_json = j_match.group(1).strip() if j_match else resp.content.strip()
            parsed = parser.parse(raw_json)
            result_data = {
                "risk_score": round(float(parsed.risk_score), 2),
                "decision": parsed.decision,
                "dispute_win_prob": round(float(parsed.dispute_win_prob), 2),
                "reasoning": parsed.reasoning,
                "recommended_action": parsed.recommended_action,
                "engine_mode": "GEMINI_2.5_FLASH_RAG"
            }
        except Exception:
            result_data = None

    if not result_data:
        result_data = statistical_fallback_scoring(req, precedents, nearest_dist)

    fraud_vector_store.add_case(
        tx_vec,
        result_data["decision"],
        result_data["risk_score"],
        f"PayPal {req.paypal_order_id}: ${req.amount_usd:.0f} ({req.dispute_claim[:50]})"
    )

    result_data["faiss_nearest_distance"] = nearest_dist
    result_data["matched_precedents"] = precedents
    result_data["paypal_dispute_evidence"] = build_paypal_dispute_evidence(
        req, result_data, precedents, nearest_dist
    )
    return result_data