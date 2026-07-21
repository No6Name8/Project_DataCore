"""
_guardrails.py  --  DataCore AI Engine: shared robustness utilities.

Provides structured logging, input validation constants, and output-contract
helpers consumed by all four models.  Import this module, never inline the
logic — one place to tighten thresholds for the whole engine.
"""

import logging
import os

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(ROOT, "models", "robustness.log")

# ── Per-model thresholds ──────────────────────────────────────────────────────
MIN_TX_CLASSIFY     = 10   # classifier: fewer rows → insufficient_history
MIN_TX_WARN         = 30   # classifier: fewer rows → low-confidence warning only
MIN_TX_FRAUD_TRAIN  = 30   # fraud: minimum rows to train a model
MIN_TX_FRAUD_SCORE  = 10   # fraud: minimum rows to score
MIN_ACTIVE_DAYS     = 14   # forecaster: fewer non-zero days → won't fit confidently
MIN_ACTIVE_DAYS_WARN = 28  # forecaster: fewer → data_quality warning

# ── SAR amount sanity bounds ──────────────────────────────────────────────────
AMT_MIN_SAR         = 0.01        # below: likely data-entry error
AMT_MAX_SAR         = 10_000_000  # above: possible enterprise data in SME pipeline
AVG_TICKET_MAX_SAR  = 2_000_000   # avg_ticket above this → scale warning


# ── Structured logger ─────────────────────────────────────────────────────────

def get_logger(model_name: str) -> logging.Logger:
    """
    Returns a Logger that writes structured records to models/robustness.log
    (DEBUG+) and to stderr (WARNING+).  Format: timestamp | model | level | msg
    """
    logger = logging.getLogger(f"datacore.{model_name}")
    if logger.handlers:          # already configured in this process
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass  # can't write log file — don't crash the model

    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    logger.propagate = False
    return logger


# ── Validation helpers ────────────────────────────────────────────────────────

def check_required_columns(df, required: list, model: str, bid: str,
                            logger: logging.Logger) -> list:
    """Returns list of missing column names, logging each."""
    missing = [c for c in required if c not in df.columns]
    for col in missing:
        logger.error(
            f"model={model} | bid={bid} | "
            f"rule=missing_required_column | column={col}"
        )
    return missing


def check_min_rows(df, minimum: int, model: str, bid: str,
                   rule: str, logger: logging.Logger) -> bool:
    """True if row count ≥ minimum; False with a WARNING log otherwise."""
    n = len(df)
    if n < minimum:
        logger.warning(
            f"model={model} | bid={bid} | rule={rule} | "
            f"actual={n} | min_required={minimum}"
        )
        return False
    return True


def check_amount_range(amounts, model: str, bid: str,
                       logger: logging.Logger) -> list:
    """
    Returns a list of warning dicts for amounts outside expected SAR range.
    Negative amounts and values above AMT_MAX_SAR are flagged.
    """
    warnings = []
    n_neg   = int((amounts < 0).sum())
    n_tiny  = int(((amounts >= 0) & (amounts < AMT_MIN_SAR)).sum())
    n_huge  = int((amounts > AMT_MAX_SAR).sum())

    if n_neg > 0:
        logger.warning(
            f"model={model} | bid={bid} | rule=negative_amounts | count={n_neg}"
        )
        warnings.append({"rule": "negative_amounts", "count": n_neg})

    if n_tiny > 0:
        logger.warning(
            f"model={model} | bid={bid} | rule=amounts_below_min_sar | "
            f"count={n_tiny} | threshold={AMT_MIN_SAR}"
        )
        warnings.append({"rule": "amounts_below_min_sar",
                         "count": n_tiny, "threshold_sar": AMT_MIN_SAR})

    if n_huge > 0:
        logger.warning(
            f"model={model} | bid={bid} | rule=value_out_of_expected_range | "
            f"count={n_huge} | threshold={AMT_MAX_SAR}"
        )
        warnings.append({"rule": "value_out_of_expected_range",
                         "count": n_huge, "threshold_sar": AMT_MAX_SAR})

    return warnings


def check_avg_ticket_range(avg_ticket: float, model: str, bid: str,
                            logger: logging.Logger) -> list:
    """Flags suspiciously large average ticket that suggests wrong-scale input."""
    warnings = []
    if avg_ticket > AVG_TICKET_MAX_SAR:
        logger.warning(
            f"model={model} | bid={bid} | rule=avg_ticket_out_of_expected_range | "
            f"avg_ticket_sar={avg_ticket:.0f} | threshold={AVG_TICKET_MAX_SAR}"
        )
        warnings.append({
            "rule":          "avg_ticket_out_of_expected_range",
            "avg_ticket_sar": avg_ticket,
            "threshold_sar":  AVG_TICKET_MAX_SAR,
        })
    return warnings


# ── Output contract builders ──────────────────────────────────────────────────

def make_data_quality(warnings: list, status: str = None) -> dict:
    """
    Standard data_quality block attached to every model output.
    status is auto-derived from warnings if not supplied:
      [] → "ok"
      non-empty → "degraded"
    """
    if status is None:
        status = "degraded" if warnings else "ok"
    return {"status": status, "warnings": warnings}


def make_insufficient_result(model: str, bid: str,
                              degraded_reason: str, detail: dict = None) -> dict:
    """
    Standard output for cases below a minimum threshold.
    Callers should return this dict directly; consumers check data_quality.status.
    """
    return {
        "status":          "insufficient_data",
        "model":           model,
        "business_id":     bid,
        "degraded_reason": degraded_reason,
        "detail":          detail or {},
        "confidence":      0.0,
        "data_quality": {
            "status":          "insufficient",
            "degraded_reason": degraded_reason,
            "warnings":        [{"rule": degraded_reason, **(detail or {})}],
        },
    }
