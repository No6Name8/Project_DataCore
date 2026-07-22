"""
counterparty_utils.py  --  DataCore AI Engine: messy payee-name normalization.

Real Saudi bank statement payee names are FREE TEXT and filthy: store numbers,
POS terminal IDs, transaction-type prefixes, mixed Arabic/English, SADAD refs.
Everything here is deliberately forgiving — it never requires an exact match,
never assumes ASCII, and never raises on weird input (returns "" / "unknown"
instead).

★ TUNING SURFACE ★  Every keyword list and regex below is data, documented, and
meant to be edited by a human when real bank data arrives. This is the file most
likely to need adjustment. Do not bury matching rules in code elsewhere.
"""

import re
from collections import Counter

# ── Thresholds (shared with the models) ───────────────────────────────────────
COUNTERPARTY_COVERAGE_MIN   = 0.20   # need ≥20% of tx to carry a counterparty
FINGERPRINT_TOKENS          = 2      # first N significant tokens form the fingerprint
INSTABILITY_RECENT_FRACTION = 0.30   # "recent" = last 30% of the ordered window
INSTABILITY_THRESHOLD       = 0.40   # >40% of distinct suppliers new-in-recent → flag
CONCENTRATION_THRESHOLD     = 0.90   # >90% of supplier tx to top-3 → concentrated

# ── Transaction-type prefixes to strip (lowercase, order-insensitive) ─────────
# Longest phrases first so "sadad bill payment" wins over "payment".
PREFIX_PHRASES = [
    "sadad bill payment", "sadad payment", "atm withdrawal", "pos purchase",
    "purchase at", "online purchase", "card purchase", "mada purchase",
    "visa purchase", "bill payment", "transfer from", "transfer to",
    "payment to", "payment for", "trf from", "trf to",
    "e-commerce", "ecommerce", "ecom", "sadad", "atm", "pos", "mada",
    "visa", "mastercard", "purchase", "payment", "debit", "credit", "ref",
]
_PREFIX_RE = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in PREFIX_PHRASES) + r")\b[\s:.\-#]*",
    re.IGNORECASE,
)

# Digit noise: latin + Arabic-Indic digits, optional leading '#', ref runs.
_DIGIT_NOISE_RE = re.compile(r"#?[\d٠-٩][\d٠-٩\-/]*")
_MULTISPACE_RE  = re.compile(r"\s+")
# Keep letters (any script), spaces; drop other punctuation.
_PUNCT_RE = re.compile(r"[^\w؀-ۿ\s]", re.UNICODE)

# Generic/article tokens dropped when choosing "significant" tokens for a fingerprint.
GENERIC_TOKENS = {
    "al", "el", "the", "a", "an", "and", "of", "for", "co", "co.", "company",
    "corp", "est", "est.", "establishment", "trading", "trad", "trade", "group",
    "llc", "ltd", "intl", "international", "services", "service", "store", "stores",
    "شركة", "مؤسسة", "مجموعة", "التجارية", "للتجارة", "و", "من", "الى", "إلى",
}

# ── Counterparty KIND controlled vocabulary (matched against the RAW upper text) ─
# bank_internal wins first (transfers), then utility, government, individual, merchant.
KIND_KEYWORDS = {
    "bank_internal": [
        "TRF FROM", "TRF TO", "TRANSFER FROM", "TRANSFER TO", "TRF ", "INTERNAL",
        "OWN ACCOUNT", "IBAN", "SA\\d", "تحويل", "حوالة",
    ],
    "utility": [
        "SADAD", "STC", "MOBILY", "ZAIN", "SEC", "SAUDI ELECTRICITY", "NWC",
        "WATER", "GAS", "ELECTRIC", "TELECOM", "INTERNET", "كهرباء", "مياه", "اتصالات",
    ],
    "government": [
        "GAZT", "ZATCA", "MOI", "MINISTRY", "MUNICIPAL", "AMANA", "ABSHER",
        "MUQEEM", "GOSI", "TRAFFIC", "PASSPORT", "VISA FEE", "وزارة", "أمانة", "بلدية",
    ],
    "individual": [
        "MR ", "MRS ", "MS ", "MISS ", "ABU ", "UMM ", "السيد", "السيدة",
    ],
}
# Compile with word boundaries where the token is short/ambiguous.
_KIND_RES = {
    kind: [re.compile(r"(?<![A-Z])" + kw + r"", re.IGNORECASE) if kw.strip().isupper() and len(kw.strip()) <= 4
           else re.compile(re.escape(kw) if not any(c in kw for c in "\\") else kw, re.IGNORECASE)
           for kw in kws]
    for kind, kws in KIND_KEYWORDS.items()
}
_HAS_LETTER_RE = re.compile(r"[A-Za-z؀-ۿ]")


# ── 1. normalize ───────────────────────────────────────────────────────────────
def normalize_counterparty(raw) -> str:
    """
    Lowercase, strip transaction-type prefixes, remove numeric/ref noise, collapse
    spaces. Arabic is preserved as-is (never transliterated). Returns "" when
    nothing meaningful survives. Never raises.
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return ""
    s = s.lower()
    # Strip a leading transaction-type phrase (repeat a couple of times for stacked prefixes).
    for _ in range(3):
        new = _PREFIX_RE.sub("", s).strip()
        if new == s:
            break
        s = new
    s = _DIGIT_NOISE_RE.sub(" ", s)
    s = _PUNCT_RE.sub(" ", s)
    s = _MULTISPACE_RE.sub(" ", s).strip()
    return s


# ── 2. fingerprint ─────────────────────────────────────────────────────────────
def counterparty_fingerprint(raw) -> str:
    """
    Stable grouping key: normalize, drop generic/article tokens, keep the first
    FINGERPRINT_TOKENS significant tokens. "STARBUCKS #4421" and "STARBUCKS 8271"
    both → "starbucks". Returns "" when nothing significant survives.
    """
    norm = normalize_counterparty(raw)
    if not norm:
        return ""
    toks = [t for t in norm.split() if len(t) >= 2 and t not in GENERIC_TOKENS]
    if not toks:                      # everything was generic/short → fall back
        toks = [t for t in norm.split() if t]
    return " ".join(toks[:FINGERPRINT_TOKENS])


# ── 3. kind classification ─────────────────────────────────────────────────────
def classify_counterparty_kind(raw) -> str:
    """
    Rule-based bucket: merchant | utility | government | individual |
    bank_internal | unknown. Matched against the RAW text (before normalization)
    so utility/transfer tokens survive. Never raises.
    """
    if raw is None:
        return "unknown"
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return "unknown"
    for kind in ("bank_internal", "utility", "government", "individual"):
        for rx in _KIND_RES[kind]:
            if rx.search(s):
                return kind
    # Anything with a real letter token left after cleaning is treated as a merchant.
    if _HAS_LETTER_RE.search(s):
        return "merchant"
    return "unknown"


# ── 4. supplier profile (order-independent) ────────────────────────────────────
def build_supplier_profile(raws) -> dict:
    """
    Aggregate a supplier profile from an iterable of raw counterparty strings
    (may contain None/empty). Coverage is reported honestly even when thin.
    """
    total = 0
    nonempty = []
    for r in raws:
        total += 1
        if r is None:
            continue
        s = str(r).strip()
        if s and s.lower() != "nan":
            nonempty.append(s)

    coverage_pct = round(len(nonempty) / total * 100, 1) if total else 0.0

    fps = [counterparty_fingerprint(s) for s in nonempty]
    fps = [f for f in fps if f]
    fp_counts = Counter(fps)
    total_fp = sum(fp_counts.values())
    top5 = fp_counts.most_common(5)
    top3 = sum(c for _, c in fp_counts.most_common(3))
    concentration = round(top3 / total_fp, 4) if total_fp else 0.0

    kinds = Counter(classify_counterparty_kind(s) for s in nonempty)
    kn = sum(kinds.values())
    kind_dist = {k: round(v / kn * 100, 1) for k, v in kinds.most_common()} if kn else {}

    return {
        "coverage_pct":                 coverage_pct,
        "total_transactions":           total,
        "transactions_with_counterparty": len(nonempty),
        "distinct_suppliers_count":     len(fp_counts),
        "top_supplier_fingerprints":    [{"fingerprint": f, "count": c} for f, c in top5],
        "supplier_kind_distribution":   kind_dist,
        "concentration_ratio":          concentration,
    }


# ── 5. supplier instability (time-ordered) ─────────────────────────────────────
def supplier_instability_ratio(raws_time_ordered,
                               recent_fraction: float = INSTABILITY_RECENT_FRACTION):
    """
    Fraction of DISTINCT suppliers whose first appearance falls in the recent
    `recent_fraction` of the ordered transaction sequence. High values = many
    brand-new payees showing up late (shell-like / money-movement pattern).
    Returns None when there are no fingerprintable counterparties.
    """
    seq = []
    for r in raws_time_ordered:
        f = counterparty_fingerprint(r)
        if f:
            seq.append(f)
    n = len(seq)
    if n == 0:
        return None
    cutoff = int(n * (1.0 - recent_fraction))   # index where the recent window starts
    first_idx = {}
    for i, f in enumerate(seq):
        first_idx.setdefault(f, i)
    distinct = len(first_idx)
    new_in_recent = sum(1 for idx in first_idx.values() if idx >= cutoff)
    return round(new_in_recent / distinct, 4) if distinct else None


if __name__ == "__main__":
    samples = [
        "STARBUCKS #4421", "POS PURCHASE 8271 AL OLAYA RIYADH",
        "شركة الراجحي للتجارة", "TAMIMI MARKETS RIYADH 03421",
        "SADAD BILL PAYMENT 8827162", "TRF FROM 1234567890",
        "STC INVOICE 4471", "GAZT ZATCA VAT", "   ", "998877",
    ]
    for s in samples:
        print(f"{s!r:45} norm={normalize_counterparty(s)!r:25} "
              f"fp={counterparty_fingerprint(s)!r:20} kind={classify_counterparty_kind(s)}")
