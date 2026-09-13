"""
Nightly job: compute a RiskFeature snapshot for every customer.

This is what feeds the "prevention, not reaction" model — it turns raw
payment/activity rows into the rolling signals (missed-payment streaks,
balance trends, early-warning flags) that both the risk model and the
chat assistant read from.

Run manually:  python risk_job.py
Schedule with cron, Airflow, a Celery beat task, etc. Idempotent per day —
re-running it the same day updates that day's snapshot rather than
duplicating it.
"""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

import models
from database import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("risk_job")

LOOKBACK_DAYS = 90
BALANCE_TREND_WINDOW_DAYS = 30

# Heuristic thresholds — tune against real outcome data once you have labels.
EARLY_WARNING_MISSED_STREAK = 2
EARLY_WARNING_PARTIAL_STREAK = 3
EARLY_WARNING_BALANCE_DROP_PCT = -20.0
DEFAULT_MISSED_STREAK = 3
DEFAULT_DAYS_LATE_THRESHOLD = 90


def _get_customer_payments(db: Session, customer_id: str) -> list[models.Payment]:
    return (
        db.query(models.Payment)
        .join(models.Account)
        .filter(models.Account.customer_id == customer_id)
        .order_by(models.Payment.due_date.asc())
        .all()
    )


def _get_activity_snapshots(db: Session, customer_id: str) -> list[models.AccountActivity]:
    return (
        db.query(models.AccountActivity)
        .filter_by(customer_id=customer_id)
        .order_by(models.AccountActivity.snapshot_date.asc())
        .all()
    )


def _trailing_streak(payments: list[models.Payment], status: models.PaymentStatus) -> int:
    """Count consecutive most-recent *resolved* payments matching status,
    stopping at the first one that doesn't match. Only considers payments
    that are actually due (skip future/unresolved ones)."""
    today = date.today()
    resolved = [p for p in payments if p.due_date <= today]
    streak = 0
    for payment in reversed(resolved):
        if payment.status == status:
            streak += 1
        else:
            break
    return streak


def _avg_days_late(payments: list[models.Payment], lookback_days: int) -> float:
    cutoff = date.today() - timedelta(days=lookback_days)
    recent = [p for p in payments if p.due_date >= cutoff and p.due_date <= date.today()]
    if not recent:
        return 0.0
    return round(sum(p.days_late for p in recent) / len(recent), 2)


def _balance_trend_pct(activities: list[models.AccountActivity], window_days: int) -> float | None:
    """% change in checking balance over the trailing window. A large
    negative number is an early-warning signal (reserves depleting)."""
    if len(activities) < 2:
        return None
    latest = activities[-1]
    cutoff = latest.snapshot_date - timedelta(days=window_days)
    baseline_candidates = [a for a in activities if a.snapshot_date <= cutoff]
    if not baseline_candidates:
        return None
    baseline = baseline_candidates[-1]
    if not baseline.checking_balance or float(baseline.checking_balance) == 0:
        return None
    latest_bal = float(latest.checking_balance or 0)
    base_bal = float(baseline.checking_balance)
    return round((latest_bal - base_bal) / abs(base_bal) * 100, 4)


def compute_risk_snapshot(db: Session, customer: models.Customer) -> dict:
    payments = _get_customer_payments(db, customer.id)
    activities = _get_activity_snapshots(db, customer.id)

    missed_streak = _trailing_streak(payments, models.PaymentStatus.MISSED)
    partial_streak = _trailing_streak(payments, models.PaymentStatus.PARTIAL)
    avg_late = _avg_days_late(payments, LOOKBACK_DAYS)
    balance_trend = _balance_trend_pct(activities, BALANCE_TREND_WINDOW_DAYS)
    hardship_flag = activities[-1].hardship_flag if activities else False

    early_warning = (
        missed_streak >= EARLY_WARNING_MISSED_STREAK
        or partial_streak >= EARLY_WARNING_PARTIAL_STREAK
        or hardship_flag
        or (balance_trend is not None and balance_trend <= EARLY_WARNING_BALANCE_DROP_PCT)
    )

    max_days_late = max((p.days_late for p in payments), default=0)
    defaulted = (
        missed_streak >= DEFAULT_MISSED_STREAK
        and max_days_late >= DEFAULT_DAYS_LATE_THRESHOLD
    )

    return {
        "consecutive_partial_payments": partial_streak,
        "missed_payment_streak": missed_streak,
        "avg_days_late_90d": avg_late,
        "balance_trend_30d": balance_trend,
        "early_warning_flag": early_warning,
        "defaulted": defaulted,
    }


def upsert_risk_feature(db: Session, customer_id: str, snapshot: dict) -> None:
    today = date.today()
    existing = (
        db.query(models.RiskFeature)
        .filter_by(customer_id=customer_id, as_of_date=today)
        .first()
    )
    if existing:
        for key, value in snapshot.items():
            setattr(existing, key, value)
    else:
        db.add(models.RiskFeature(customer_id=customer_id, as_of_date=today, **snapshot))


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        customers = db.query(models.Customer).all()
        logger.info("Computing risk features for %d customers", len(customers))
        for customer in customers:
            snapshot = compute_risk_snapshot(db, customer)
            upsert_risk_feature(db, customer.id, snapshot)
            if snapshot["early_warning_flag"]:
                logger.info("Early warning flagged for customer %s", customer.id)
        db.commit()
        logger.info("Done.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
