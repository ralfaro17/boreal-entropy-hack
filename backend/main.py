from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db, init_db

app = FastAPI(title="Bank Debt-Prevention Demo")


@app.on_event("startup")
def on_startup():
    init_db()


# --- Customers -------------------------------------------------------------

@app.post("/customers", response_model=schemas.CustomerOut)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    customer = models.Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@app.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer


# --- Accounts ----------------------------------------------------------------

@app.post("/accounts", response_model=schemas.AccountOut)
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)):
    account = models.Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.get("/customers/{customer_id}/accounts", response_model=list[schemas.AccountOut])
def list_customer_accounts(customer_id: str, db: Session = Depends(get_db)):
    return db.query(models.Account).filter_by(customer_id=customer_id).all()


# --- Payments ----------------------------------------------------------------

@app.post("/payments", response_model=schemas.PaymentOut)
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db)):
    payment = models.Payment(**payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@app.get("/accounts/{account_id}/payments", response_model=list[schemas.PaymentOut])
def list_account_payments(account_id: str, db: Session = Depends(get_db)):
    return db.query(models.Payment).filter_by(account_id=account_id).all()


# --- Account activity ---------------------------------------------------------

@app.post("/account-activity")
def create_activity(payload: schemas.AccountActivityCreate, db: Session = Depends(get_db)):
    activity = models.AccountActivity(**payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return {"id": activity.id}


# --- Risk features (read-only here; assume a separate job computes them) -----

@app.get("/customers/{customer_id}/risk-features", response_model=list[schemas.RiskFeatureOut])
def list_risk_features(customer_id: str, db: Session = Depends(get_db)):
    return db.query(models.RiskFeature).filter_by(customer_id=customer_id).all()


@app.get("/customers/{customer_id}/early-warning")
def early_warning_status(customer_id: str, db: Session = Depends(get_db)):
    """Simple example of a prevention-oriented endpoint: flags customers
    currently showing early-warning signals, instead of waiting for default."""
    latest = (
        db.query(models.RiskFeature)
        .filter_by(customer_id=customer_id)
        .order_by(models.RiskFeature.as_of_date.desc())
        .first()
    )
    if not latest:
        raise HTTPException(404, "No risk data for this customer")
    return {
        "customer_id": customer_id,
        "as_of_date": latest.as_of_date,
        "early_warning_flag": latest.early_warning_flag,
        "missed_payment_streak": latest.missed_payment_streak,
        "consecutive_partial_payments": latest.consecutive_partial_payments,
    }