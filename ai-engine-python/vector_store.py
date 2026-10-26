import os
import json
import math
import faiss
import numpy as np
from threading import Lock
from typing import List, Dict, Any, Tuple

INDEX_DIR = os.getenv("FAISS_INDEX_DIR", "/app/faiss_index")
INDEX_PATH = os.path.join(INDEX_DIR, "fintech_risk.index")
META_PATH = os.path.join(INDEX_DIR, "fintech_metadata.json")

def encode_tx_vector(amount_usd: float, velocity_1h: int, cross_border: bool, cb_rate: float) -> List[float]:
    return [
        round(math.log10(max(amount_usd, 1.0) + 1.0), 4),
        round(min(velocity_1h / 10.0, 10.0), 4),
        2.0 if cross_border else 0.0,
        round(cb_rate, 4)
    ]

class FraudVectorStore:
    def __init__(self):
        self.dim = 4
        self.lock = Lock()
        self.metadata: List[Dict[str, Any]] = []
        self._load_or_initialize()

    def _load_or_initialize(self):
        os.makedirs(INDEX_DIR, exist_ok=True)
        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            self.index = faiss.read_index(INDEX_PATH)
            with open(META_PATH, "r") as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            seed_cases = [
                {
                    "amount": 2400.0, "vel": 22, "xb": True, "cb": 2.4,
                    "label": "PAYPAL_UNAUTHORIZED_CNP_BURST", "historical_score": 92.5,
                    "summary": "High-velocity cross-border PayPal guest checkout carding burst"
                },
                {
                    "amount": 1450.0, "vel": 15, "xb": True, "cb": 1.8,
                    "label": "PAYPAL_INR_FRIENDLY_FRAUD", "historical_score": 76.0,
                    "summary": "PayPal Item Not Received (INR) dispute on digital license with IP mismatch"
                },
                {
                    "amount": 49.0, "vel": 2, "xb": False, "cb": 0.3,
                    "label": "PAYPAL_BILLING_AGREEMENT_SAFE", "historical_score": 8.5,
                    "summary": "Verified recurring domestic PayPal subscription settlement"
                },
                {
                    "amount": 320.0, "vel": 6, "xb": True, "cb": 0.9,
                    "label": "PAYPAL_3DS2_STEP_UP_CLEARED", "historical_score": 48.0,
                    "summary": "Cross-border PayPal checkout cleared via Payer Action 3DSecure 2.2"
                },
                {
                    "amount": 5800.0, "vel": 30, "xb": True, "cb": 3.5,
                    "label": "SYNTHETIC_ACCOUNT_TAKEOVER", "historical_score": 97.0,
                    "summary": "Rapid high-ticket PayPal merchant payout drain from proxy ASN"
                },
                {
                    "amount": 18.5, "vel": 1, "xb": False, "cb": 0.15,
                    "label": "PAYPAL_SELLER_PROTECTED_OK", "historical_score": 4.0,
                    "summary": "Domestic PayPal Express Checkout eligible for full Seller Protection"
                }
            ]
            vectors = []
            for c in seed_cases:
                vec = encode_tx_vector(c["amount"], c["vel"], c["xb"], c["cb"])
                vectors.append(vec)
                self.metadata.append({
                    "label": c["label"],
                    "historical_score": c["historical_score"],
                    "summary": c["summary"],
                    "vector": vec
                })
            self.index.add(np.array(vectors, dtype=np.float32))
            self._persist()

    def _persist(self):
        faiss.write_index(self.index, INDEX_PATH)
        with open(META_PATH, "w") as f:
            json.dump(self.metadata, f)

    def search_precedents(self, query_vec: List[float], k: int = 3) -> Tuple[float, List[Dict[str, Any]]]:
        with self.lock:
            if self.index.ntotal == 0:
                return 0.0, []
            k_actual = min(k, self.index.ntotal)
            vec = np.array([query_vec], dtype=np.float32)
            distances, indices = self.index.search(vec, k_actual)
            matches = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx != -1:
                    entry = dict(self.metadata[idx])
                    entry["l2_distance"] = round(float(dist), 4)
                    matches.append(entry)
            nearest_dist = round(float(distances[0][0]), 4) if len(distances[0]) > 0 else 0.0
            return nearest_dist, matches

    def add_case(self, query_vec: List[float], label: str, score: float, summary: str):
        with self.lock:
            vec = np.array([query_vec], dtype=np.float32)
            self.index.add(vec)
            self.metadata.append({
                "label": label,
                "historical_score": round(float(score), 2),
                "summary": summary[:160],
                "vector": query_vec
            })
            self._persist()

    def total_entries(self) -> int:
        return int(self.index.ntotal)

fraud_vector_store = FraudVectorStore()