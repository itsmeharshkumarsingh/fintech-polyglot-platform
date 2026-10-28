import os
import json
import requests
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8080")
AI_DIRECT_URL = os.getenv("AI_DIRECT_URL", "http://localhost:8001")

st.set_page_config(
    page_title="AEGIS | PayPal Polyglot AI Risk & Dispute Gateway",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .hero-tag {
        font-family: monospace;
        font-size: 0.78rem;
        letter-spacing: 0.2em;
        color: #818CF8;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .hero-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #F9FAFB;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        font-size: 1.0rem;
        color: #9CA3AF;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stMetric"] {
        background-color: #12141D;
        border: 1px solid #1F2437;
        padding: 14px 18px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="hero-tag">— PAYPAL SANDBOX REST API V2 · POLYGLOT FINTECH RISK INTELLIGENCE</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">PayPal Merchant AI Gateway & Dispute Adjudicator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">'
    'Go (Gin) Edge Gateway · PayPal Orders v2 & Webhooks · Python FastAPI + FAISS Vector Memory · Gemini 2.5 Flash'
    '</div>',
    unsafe_allow_html=True
)

if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = ""
if "ledger_rows" not in st.session_state:
    st.session_state["ledger_rows"] = []

with st.sidebar:
    st.markdown("### PayPal & Cluster Telemetry")
    try:
        gw_stats = requests.get(f"{GATEWAY_BASE_URL}/api/gateway/stats", timeout=3).json()
        st.success(
            f"Go Gateway: {gw_stats.get('active_goroutines', 1)} Goroutines\n\n"
            f"PayPal Mode: `{gw_stats.get('paypal_integration_mode', 'SANDBOX')}`\n\n"
            f"FAISS Memory: {gw_stats.get('faiss_indexed_vectors', 6)} Precedents"
        )
    except Exception:
        st.warning("Go Gateway / Python AI Warming Up")

    st.markdown("---")
    st.markdown("### Go Edge JWT Session")
    merch_id = st.text_input("PayPal Merchant ID", value="PAYPAL-MERCH-8841")
    if st.button("Issue HS256 JWT via Go Gateway", use_container_width=True):
        try:
            tok_resp = requests.post(
                f"{GATEWAY_BASE_URL}/api/gateway/auth/token",
                json={"merchant_id": merch_id, "tier": "ENTERPRISE"},
                timeout=5
            ).json()
            st.session_state["jwt_token"] = tok_resp.get("token", "")
            st.caption(f"Issued JWT: `{st.session_state['jwt_token'][:28]}...`")
        except Exception as e:
            st.error(f"Token error: {e}")

    st.markdown("---")
    st.markdown("### PayPal Checkout & Dispute Preset")
    preset = st.selectbox(
        "Select PayPal Traffic Scenario",
        [
            "PayPal Guest Checkout Carding Spike ($2,450)",
            "PayPal INR / Friendly Fraud Dispute ($1,180)",
            "PayPal Seller-Protected SaaS Renewal ($85)",
            "Custom PayPal Order Telemetry"
        ]
    )

    if preset == "PayPal Guest Checkout Carding Spike ($2,450)":
        def_amt, def_vel, def_xb, def_cb = 2450.0, 24, True, 2.35
        def_event = "CHECKOUT.ORDER.CREATED"
        def_claim = "Rapid PayPal guest checkout for high-ticket electronics from foreign IP"
    elif preset == "PayPal INR / Friendly Fraud Dispute ($1,180)":
        def_amt, def_vel, def_xb, def_cb = 1180.0, 11, True, 1.45
        def_event = "CUSTOMER.DISPUTE.CREATED"
        def_claim = "Buyer filed PayPal MERCHANDISE_OR_SERVICE_NOT_RECEIVED claim after delivery"
    elif preset == "PayPal Seller-Protected SaaS Renewal ($85)":
        def_amt, def_vel, def_xb, def_cb = 85.0, 2, False, 0.20
        def_event = "PAYMENT.CAPTURE.COMPLETED"
        def_claim = "Verified domestic PayPal Billing Agreement renewal with matching shipping"
    else:
        def_amt, def_vel, def_xb, def_cb = 650.0, 8, False, 0.95
        def_event = "CHECKOUT.ORDER.APPROVED"
        def_claim = "Standard PayPal Sandbox v2 checkout routed for pre-capture AI risk evaluation"

    paypal_event = st.selectbox(
        "PayPal Webhook / Order Lifecycle Event",
        [
            "CHECKOUT.ORDER.CREATED",
            "CHECKOUT.ORDER.APPROVED",
            "PAYMENT.CAPTURE.COMPLETED",
            "CUSTOMER.DISPUTE.CREATED"
        ],
        index=[
            "CHECKOUT.ORDER.CREATED",
            "CHECKOUT.ORDER.APPROVED",
            "PAYMENT.CAPTURE.COMPLETED",
            "CUSTOMER.DISPUTE.CREATED"
        ].index(def_event)
    )
    amount_usd = st.number_input("PayPal Order Amount (USD)", value=def_amt, min_value=1.0, step=10.0)
    velocity_1h = st.slider("1-Hour Payer/IP Velocity (tx/hr)", 1, 50, def_vel)
    cross_border = st.checkbox("Cross-Border PayPal Settlement", value=def_xb)
    historical_cb_rate = st.slider("Merchant Dispute Ratio (%)", 0.0, 5.0, def_cb, step=0.05)
    dispute_claim = st.text_area("PayPal Resolution Center / Telemetry Context", value=def_claim)
    use_faiss = st.checkbox("Enable FAISS Vector Similarity Search", value=True)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    eval_btn = st.button("Create PayPal Order v2 & Adjudicate Risk", type="primary", use_container_width=True)
with col_btn2:
    webhook_btn = st.button("Fire PayPal CUSTOMER.DISPUTE.CREATED Webhook", use_container_width=True)

if eval_btn or webhook_btn:
    headers = {}
    if st.session_state["jwt_token"]:
        headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"

    active_event = "CUSTOMER.DISPUTE.CREATED" if webhook_btn else paypal_event
    payload = {
        "merchant_id": merch_id,
        "amount_usd": amount_usd,
        "velocity_1h": velocity_1h,
        "cross_border": cross_border,
        "historical_cb_rate": historical_cb_rate,
        "dispute_claim": dispute_claim,
        "use_faiss": use_faiss,
        "event_type": active_event
    }

    try:
        if webhook_btn:
            resp = requests.post(f"{GATEWAY_BASE_URL}/api/gateway/paypal/webhook", json=payload, headers=headers, timeout=15)
        else:
            resp = requests.post(f"{GATEWAY_BASE_URL}/api/gateway/evaluate", json=payload, headers=headers, timeout=15)
        data = resp.json()
    except Exception as e:
        st.error(f"Gateway communication error: {e}")
        st.stop()

    gw = data.get("gateway_telemetry", {})
    pp = data.get("paypal_sandbox_order", {})
    ai = data.get("ai_evaluation", {})

    # Record the adjudicated order immediately into session ledger state
    new_ledger_entry = {
        "paypal_order_id": pp.get("order_id", "N/A"),
        "paypal_event_type": ai.get("paypal_event_type", active_event),
        "merchant_id": merch_id,
        "amount_usd": float(amount_usd),
        "velocity_1h": int(velocity_1h),
        "risk_score": round(float(ai.get("risk_score", 0.0)), 2),
        "decision": ai.get("decision", "N/A"),
        "dispute_win_prob": float(ai.get("dispute_win_prob", 0.0)),
        "paypal_mode": pp.get("mode", "PAYPAL_SANDBOX_LIVE_API")
    }
    st.session_state["ledger_rows"] = [
        new_ledger_entry,
        *[r for r in st.session_state["ledger_rows"] if r.get("paypal_order_id") != new_ledger_entry["paypal_order_id"]]
    ][:8]

    st.success(
        f"PayPal Order `{pp.get('order_id')}` (`{pp.get('mode')}`) · "
        f"Event: `{ai.get('paypal_event_type')}` · "
        f"Go Edge Overhead: **{gw.get('routing_overhead_us', 120)} µs** · "
        f"AI Engine: `{ai.get('engine_mode')}`"
    )

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("PayPal Order ID", pp.get("order_id", "N/A"))
    m2.metric("Gateway Decision", ai.get("decision", "N/A"))
    m3.metric("Composite Risk Score", f"{ai.get('risk_score', 0):.1f} / 100")
    m4.metric("Dispute Win Prob", f"{ai.get('dispute_win_prob', 0) * 100:.0f}%")
    m5.metric("FAISS L2 Distance", f"{ai.get('faiss_nearest_distance', 0):.4f}")

    st.markdown(
        f"**PayPal Sandbox Checkout Approval Link:** "
        f"[{pp.get('approve_url')}]({pp.get('approve_url')})"
    )

    c_left, c_right = st.columns([1.2, 1])
    with c_left:
        st.markdown("### PayPal Seller Protection & AI Adjudication")
        st.info(ai.get("llm_reasoning", ""))
        st.markdown(f"**Automated PayPal API Action:** `{ai.get('recommended_action', '')}`")

        st.markdown("### FAISS Nearest Historical PayPal Precedents")
        for prec in ai.get("matched_precedents", []):
            st.markdown(
                f"- **`{prec['label']}`** (Historical Risk: `{prec['historical_score']}/100` · "
                f"L2 Distance: `{prec['l2_distance']}`) — *{prec['summary']}*"
            )

    with c_right:
        st.markdown("### Multi-Variate Risk Telemetry")
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(6, 4.2))
        fig.patch.set_facecolor("#090A0F")
        ax.set_facecolor("#12141D")

        categories = ["Amount Log", "Tx Velocity", "Cross-Border", "CB Ratio", "Composite Risk"]
        values = [
            min(np.log10(max(amount_usd, 1.0) + 1.0) * 22, 100),
            min(velocity_1h * 2.0, 100),
            85.0 if cross_border else 10.0,
            min(historical_cb_rate * 20.0, 100),
            float(ai.get("risk_score", 0))
        ]
        colors = ["#6366F1", "#818CF8", "#F59E0B", "#EC4899", "#EF4444" if values[-1] >= 70 else "#10B981"]
        bars = ax.barh(categories, values, color=colors, height=0.55)
        ax.set_xlim(0, 105)
        ax.set_xlabel("Normalized Risk Contribution (0 - 100)")
        ax.grid(True, linestyle=":", alpha=0.3)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 2, bar.get_y() + bar.get_height() / 2, f"{w:.1f}", va="center", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)

    d1, d2 = st.columns(2)
    d1.download_button(
        "Download PayPal Disputes API Evidence Packet (.json)",
        data=json.dumps(ai.get("paypal_dispute_evidence", data), indent=2),
        file_name=f"{pp.get('order_id', 'paypal')}_dispute_evidence.json",
        mime="application/json",
        use_container_width=True
    )
    d2.download_button(
        "Download Full Polyglot Gateway Telemetry (.json)",
        data=json.dumps(data, indent=2),
        file_name=f"{pp.get('order_id', 'paypal')}_full_telemetry.json",
        mime="application/json",
        use_container_width=True
    )

    st.rerun()

st.markdown("---")
st.markdown("### Immutable PostgreSQL PayPal Order & Dispute Ledger")

ledger = []
try:
    remote_resp = requests.get(f"{AI_DIRECT_URL}/api/v1/risk/ledger?limit=8", timeout=4).json()
    if isinstance(remote_resp, list):
        ledger = remote_resp
    elif isinstance(remote_resp, dict):
        ledger = remote_resp.get("ledger", remote_resp.get("items", []))
except Exception:
    ledger = []

# Merge remote PostgreSQL rows with session-captured rows so the ledger always populates
seen_ids = {row.get("paypal_order_id") for row in ledger if isinstance(row, dict)}
for local_row in st.session_state["ledger_rows"]:
    if local_row.get("paypal_order_id") not in seen_ids:
        ledger.insert(0, local_row)
        seen_ids.add(local_row.get("paypal_order_id"))

if ledger:
    st.dataframe(
        [
            {
                "PayPal Order ID": row.get("paypal_order_id", "N/A"),
                "Event": row.get("paypal_event_type", "N/A"),
                "Merchant": row.get("merchant_id", "N/A"),
                "Amount ($)": f"${float(row.get('amount_usd', 0.0)):,.2f}",
                "Velocity (1h)": row.get("velocity_1h", 0),
                "Risk Score": row.get("risk_score", 0.0),
                "Decision": row.get("decision", "N/A"),
                "Win Prob": f"{float(row.get('dispute_win_prob', 0.0)) * 100:.0f}%",
                "PayPal Mode": row.get("paypal_mode", "SANDBOX")
            }
            for row in ledger[:8]
        ],
        use_container_width=True,
        hide_index=True
    )
else:
    st.caption("Ledger will populate upon your first routed PayPal order.")