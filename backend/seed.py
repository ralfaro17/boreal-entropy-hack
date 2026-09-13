"""
Database seeder for Boreal Entropy demo personas.

Usage:
    uv run python seed.py          # Seeds the 10 demo personas if not present
    uv run python seed.py --reset  # Clears and re-seeds all demo data
"""

import argparse
import logging
from sqlalchemy import delete
from sqlalchemy.orm import Session

from database import SessionLocal, init_db
import demo_data
import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("seed")


def clean_database(db: Session) -> None:
    """Delete all mock data in foreign-key dependency order."""
    logger.info("Cleaning up mock demo records...")
    db.execute(delete(models.Message))
    db.execute(delete(models.Conversation))
    db.execute(delete(models.RiskFeature))
    db.execute(delete(models.AccountActivity))
    db.execute(delete(models.Payment))
    db.execute(delete(models.Account))
    db.execute(delete(models.Customer))
    db.commit()
    logger.info("Database cleaned successfully.")


def seed_database(db: Session, reset: bool = False) -> dict[str, int]:
    """Seed the 10 demo customer personas with accounts, payments, activities,

    risk features, and historical conversation threads.
    """
    if reset:
        clean_database(db)

    # Check if demo data is already present (idempotency check)
    existing_count = db.query(models.Customer).count()
    if existing_count > 0 and not reset:
        logger.info("Database already contains %d customers. Skipping seed (use --reset to overwrite).", existing_count)
        return {"skipped": existing_count}

    dataset = demo_data.get_demo_dataset()

    for customer in dataset["customers"]:
        db.add(customer)
    for account in dataset["accounts"]:
        db.add(account)
    for payment in dataset["payments"]:
        db.add(payment)
    for activity in dataset["activities"]:
        db.add(activity)
    for risk_feature in dataset["risk_features"]:
        db.add(risk_feature)
    for conversation in dataset["conversations"]:
        db.add(conversation)
    for message in dataset["messages"]:
        db.add(message)

    db.commit()

    stats = {
        "customers": len(dataset["customers"]),
        "accounts": len(dataset["accounts"]),
        "payments": len(dataset["payments"]),
        "activities": len(dataset["activities"]),
        "risk_features": len(dataset["risk_features"]),
        "conversations": len(dataset["conversations"]),
        "messages": len(dataset["messages"]),
    }

    logger.info("Successfully seeded demo data: %s", stats)
    return stats


def main():
    parser = argparse.ArgumentParser(description="Seed demo mockup data for Boreal Entropy.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe existing demo data before seeding",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        seed_database(db, reset=args.reset)
    finally:
        db.close()


if __name__ == "__main__":
    main()

