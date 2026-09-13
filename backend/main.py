import json
import os
import re
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any

import models
import schemas
from anthropic import AsyncAnthropic
from chat import chat_manager
from database import SessionLocal, check_db_connection, get_db, init_db
from guardrails import (
    check_compliance_violations,
    customer_message_signals_distress,
    detect_customer_distress,
    get_escalation_reply,
    output_violates_guardrails,
    validate_compliance_or_raise,
)
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Bank Debt-Prevention API",
    description="REST API for customer credit, loan accounts, payment tracking, behavioral activity, and debt-prevention risk features.",
    version="1.0.0",
    lifespan=lifespan,
)


# ===========================================================================
# System & Health
# ===========================================================================

@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to Bank Debt-Prevention API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["System"])
def health_check():
    is_connected = check_db_connection()
    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        )
    return {"status": "ok", "database": "connected"}


# ===========================================================================
# Customers
# ===========================================================================

@app.post(
    "/customers",
    response_model=schemas.CustomerOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Customers"],
)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(models.Customer).filter_by(email=payload.email)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email '{payload.email}' already exists",
        )

    customer = models.Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@app.get(
    "/customers",
    response_model=list[schemas.CustomerOut],
    tags=["Customers"],
)
def list_customers(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max items to return"),
    email: str | None = Query(None, description="Filter by exact email"),
    region: str | None = Query(None, description="Filter by region"),
    employment_status: models.EmploymentStatus | None = Query(
        None, description="Filter by employment status"
    ),
    db: Session = Depends(get_db),
):
    query = select(models.Customer)
    if email is not None:
        query = query.filter_by(email=email)
    if region is not None:
        query = query.filter_by(region=region)
    if employment_status is not None:
        query = query.filter_by(employment_status=employment_status)

    query = query.offset(skip).limit(limit)
    return db.execute(query).scalars().all()


@app.get(
    "/customers/{customer_id}",
    response_model=schemas.CustomerOut,
    tags=["Customers"],
)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


@app.put(
    "/customers/{customer_id}",
    response_model=schemas.CustomerOut,
    tags=["Customers"],
)
@app.patch(
    "/customers/{customer_id}",
    response_model=schemas.CustomerOut,
    tags=["Customers"],
)
def update_customer(
    customer_id: str,
    payload: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] != customer.email:
        existing = db.execute(
            select(models.Customer).filter_by(email=update_data["email"])
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer with email '{update_data['email']}' already exists",
            )

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


@app.delete(
    "/customers/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Customers"],
)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    db.delete(customer)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Accounts
# ===========================================================================

@app.post(
    "/accounts",
    response_model=schemas.AccountOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Accounts"],
)
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, payload.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer '{payload.customer_id}' not found",
        )

    account = models.Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.get(
    "/accounts",
    response_model=list[schemas.AccountOut],
    tags=["Accounts"],
)
def list_accounts(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max items to return"),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    product_type: models.ProductType | None = Query(None, description="Filter by product type"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    query = select(models.Account)
    if customer_id is not None:
        query = query.filter_by(customer_id=customer_id)
    if product_type is not None:
        query = query.filter_by(product_type=product_type)
    if is_active is not None:
        query = query.filter_by(is_active=is_active)

    query = query.offset(skip).limit(limit)
    return db.execute(query).scalars().all()


@app.get(
    "/customers/{customer_id}/accounts",
    response_model=list[schemas.AccountOut],
    tags=["Accounts"],
)
def list_customer_accounts(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return db.execute(
        select(models.Account).filter_by(customer_id=customer_id)
    ).scalars().all()


@app.get(
    "/accounts/{account_id}",
    response_model=schemas.AccountOut,
    tags=["Accounts"],
)
def get_account(account_id: str, db: Session = Depends(get_db)):
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@app.put(
    "/accounts/{account_id}",
    response_model=schemas.AccountOut,
    tags=["Accounts"],
)
@app.patch(
    "/accounts/{account_id}",
    response_model=schemas.AccountOut,
    tags=["Accounts"],
)
def update_account(
    account_id: str,
    payload: schemas.AccountUpdate,
    db: Session = Depends(get_db),
):
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account


@app.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Accounts"],
)
def delete_account(account_id: str, db: Session = Depends(get_db)):
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    db.delete(account)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Payments
# ===========================================================================

@app.post(
    "/payments",
    response_model=schemas.PaymentOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Payments"],
)
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db)):
    account = db.get(models.Account, payload.account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account '{payload.account_id}' not found",
        )

    payment = models.Payment(**payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@app.get(
    "/payments",
    response_model=list[schemas.PaymentOut],
    tags=["Payments"],
)
def list_payments(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max items to return"),
    account_id: str | None = Query(None, description="Filter by account ID"),
    status: models.PaymentStatus | None = Query(None, description="Filter by payment status"),
    db: Session = Depends(get_db),
):
    query = select(models.Payment)
    if account_id is not None:
        query = query.filter_by(account_id=account_id)
    if status is not None:
        query = query.filter_by(status=status)

    query = query.offset(skip).limit(limit)
    return db.execute(query).scalars().all()


@app.get(
    "/accounts/{account_id}/payments",
    response_model=list[schemas.PaymentOut],
    tags=["Payments"],
)
def list_account_payments(account_id: str, db: Session = Depends(get_db)):
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return db.execute(
        select(models.Payment).filter_by(account_id=account_id)
    ).scalars().all()


@app.get(
    "/payments/{payment_id}",
    response_model=schemas.PaymentOut,
    tags=["Payments"],
)
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = db.get(models.Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment


@app.put(
    "/payments/{payment_id}",
    response_model=schemas.PaymentOut,
    tags=["Payments"],
)
@app.patch(
    "/payments/{payment_id}",
    response_model=schemas.PaymentOut,
    tags=["Payments"],
)
def update_payment(
    payment_id: str,
    payload: schemas.PaymentUpdate,
    db: Session = Depends(get_db),
):
    payment = db.get(models.Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    return payment


@app.delete(
    "/payments/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Payments"],
)
def delete_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = db.get(models.Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    db.delete(payment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Account Activity
# ===========================================================================

@app.post(
    "/account-activity",
    response_model=schemas.AccountActivityOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Account Activity"],
)
def create_activity(
    payload: schemas.AccountActivityCreate,
    db: Session = Depends(get_db),
):
    customer = db.get(models.Customer, payload.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer '{payload.customer_id}' not found",
        )

    activity = models.AccountActivity(**payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@app.get(
    "/account-activity",
    response_model=list[schemas.AccountActivityOut],
    tags=["Account Activity"],
)
def list_activities(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max items to return"),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    hardship_flag: bool | None = Query(None, description="Filter by hardship flag"),
    large_withdrawal_flag: bool | None = Query(None, description="Filter by large withdrawal flag"),
    db: Session = Depends(get_db),
):
    query = select(models.AccountActivity)
    if customer_id is not None:
        query = query.filter_by(customer_id=customer_id)
    if hardship_flag is not None:
        query = query.filter_by(hardship_flag=hardship_flag)
    if large_withdrawal_flag is not None:
        query = query.filter_by(large_withdrawal_flag=large_withdrawal_flag)

    query = query.order_by(models.AccountActivity.snapshot_date.desc()).offset(skip).limit(limit)
    return db.execute(query).scalars().all()


@app.get(
    "/customers/{customer_id}/account-activity",
    response_model=list[schemas.AccountActivityOut],
    tags=["Account Activity"],
)
def list_customer_activities(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return db.execute(
        select(models.AccountActivity)
        .filter_by(customer_id=customer_id)
        .order_by(models.AccountActivity.snapshot_date.desc())
    ).scalars().all()


@app.get(
    "/account-activity/{activity_id}",
    response_model=schemas.AccountActivityOut,
    tags=["Account Activity"],
)
def get_activity(activity_id: str, db: Session = Depends(get_db)):
    activity = db.get(models.AccountActivity, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account activity record not found",
        )
    return activity


@app.put(
    "/account-activity/{activity_id}",
    response_model=schemas.AccountActivityOut,
    tags=["Account Activity"],
)
@app.patch(
    "/account-activity/{activity_id}",
    response_model=schemas.AccountActivityOut,
    tags=["Account Activity"],
)
def update_activity(
    activity_id: str,
    payload: schemas.AccountActivityUpdate,
    db: Session = Depends(get_db),
):
    activity = db.get(models.AccountActivity, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account activity record not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity


@app.delete(
    "/account-activity/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Account Activity"],
)
def delete_activity(activity_id: str, db: Session = Depends(get_db)):
    activity = db.get(models.AccountActivity, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account activity record not found",
        )
    db.delete(activity)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ===========================================================================
# Risk Features
# ===========================================================================

@app.post(
    "/risk-features",
    response_model=schemas.RiskFeatureOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Risk Features"],
)
def create_risk_feature(
    payload: schemas.RiskFeatureCreate,
    db: Session = Depends(get_db),
):
    customer = db.get(models.Customer, payload.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer '{payload.customer_id}' not found",
        )

    feature = models.RiskFeature(**payload.model_dump())
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return feature


@app.get(
    "/risk-features",
    response_model=list[schemas.RiskFeatureOut],
    tags=["Risk Features"],
)
def list_risk_features_all(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max items to return"),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    early_warning_flag: bool | None = Query(None, description="Filter by early warning flag"),
    defaulted: bool | None = Query(None, description="Filter by defaulted status"),
    db: Session = Depends(get_db),
):
    query = select(models.RiskFeature)
    if customer_id is not None:
        query = query.filter_by(customer_id=customer_id)
    if early_warning_flag is not None:
        query = query.filter_by(early_warning_flag=early_warning_flag)
    if defaulted is not None:
        query = query.filter_by(defaulted=defaulted)

    query = query.order_by(models.RiskFeature.as_of_date.desc()).offset(skip).limit(limit)
    return db.execute(query).scalars().all()


@app.get(
    "/customers/{customer_id}/risk-features",
    response_model=list[schemas.RiskFeatureOut],
    tags=["Risk Features"],
)
def list_customer_risk_features(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return db.execute(
        select(models.RiskFeature)
        .filter_by(customer_id=customer_id)
        .order_by(models.RiskFeature.as_of_date.desc())
    ).scalars().all()


@app.get(
    "/risk-features/{feature_id}",
    response_model=schemas.RiskFeatureOut,
    tags=["Risk Features"],
)
def get_risk_feature(feature_id: str, db: Session = Depends(get_db)):
    feature = db.get(models.RiskFeature, feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk feature record not found",
        )
    return feature


@app.put(
    "/risk-features/{feature_id}",
    response_model=schemas.RiskFeatureOut,
    tags=["Risk Features"],
)
@app.patch(
    "/risk-features/{feature_id}",
    response_model=schemas.RiskFeatureOut,
    tags=["Risk Features"],
)
def update_risk_feature(
    feature_id: str,
    payload: schemas.RiskFeatureUpdate,
    db: Session = Depends(get_db),
):
    feature = db.get(models.RiskFeature, feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk feature record not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(feature, field, value)

    db.commit()
    db.refresh(feature)
    return feature


@app.delete(
    "/risk-features/{feature_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Risk Features"],
)
def delete_risk_feature(feature_id: str, db: Session = Depends(get_db)):
    feature = db.get(models.RiskFeature, feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk feature record not found",
        )
    db.delete(feature)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/customers/{customer_id}/early-warning", tags=["Risk Features"])
def early_warning_status(customer_id: str, db: Session = Depends(get_db)):
    """Flags customers currently showing early-warning signals instead of waiting for default."""
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    latest = db.execute(
        select(models.RiskFeature)
        .filter_by(customer_id=customer_id)
        .order_by(models.RiskFeature.as_of_date.desc())
    ).scalars().first()

    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk data for this customer",
        )

    return {
        "customer_id": customer_id,
        "as_of_date": latest.as_of_date,
        "early_warning_flag": latest.early_warning_flag,
        "missed_payment_streak": latest.missed_payment_streak,
        "consecutive_partial_payments": latest.consecutive_partial_payments,
        "debt_to_income_ratio": float(latest.debt_to_income_ratio)
        if latest.debt_to_income_ratio is not None
        else None,
        "credit_utilization_pct": float(latest.credit_utilization_pct)
        if latest.credit_utilization_pct is not None
        else None,
        "balance_trend_30d": float(latest.balance_trend_30d)
        if latest.balance_trend_30d is not None
        else None,
    }


# ===========================================================================
# WebSocket & WhatsApp-Style Chat Rooms (Backed by Persistent Conversation)
# ===========================================================================

ai_client = None
if os.getenv("ANTHROPIC_API_KEY"):
    try:
        ai_client = AsyncAnthropic()
    except Exception:
        ai_client = None

def get_or_create_active_conversation(db: Session, customer_id: str) -> models.Conversation:
    """Retrieve an ongoing conversation from the last 14 days, or create a new one."""
    cutoff = datetime.utcnow() - timedelta(days=14)
    convo = (
        db.query(models.Conversation)
        .filter(models.Conversation.customer_id == customer_id)
        .filter(models.Conversation.last_message_at >= cutoff)
        .order_by(models.Conversation.last_message_at.desc())
        .first()
    )
    if convo:
        return convo

    convo = models.Conversation(
        customer_id=customer_id,
        started_at=datetime.utcnow(),
        last_message_at=datetime.utcnow(),
        channel=models.Channel.APP,
        is_escalated=False,
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def record_conversation_event(
    db: Session,
    conversation_id: str,
    event_type: models.ConversationEventType,
    title: str,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> models.ConversationEvent:
    """Record a regulatory or compliance audit milestone in the dedicated conversation_events table.
    Ensures compliance audits and supervisor timelines are fully documented without polluting
    the Message table or LLM context windows.
    """
    event = models.ConversationEvent(
        conversation_id=conversation_id,
        event_type=event_type,
        title=title,
        description=description,
        metadata_json=json.dumps(metadata) if metadata else None,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


async def generate_risk_reminder(
    customer: models.Customer,
    payment: models.Payment,
    risk: models.RiskFeature | None,
    activity: models.AccountActivity | None,
    language: str = "es",
) -> str:
    """Generate a non-judgmental, compliant debt-prevention reminder."""
    amount_due = float(payment.amount_due)
    due_date_str = (
        payment.due_date.strftime("%d/%m/%Y")
        if language == "es"
        else payment.due_date.strftime("%b %d, %Y")
    )
    days_until_due = (payment.due_date - date.today()).days
    hardship = activity.hardship_flag if activity else False
    streak = risk.missed_payment_streak if risk else 0

    is_overdue = days_until_due < 0
    days_desc = f"{abs(days_until_due)} días atrasado" if is_overdue else f"{days_until_due} días restantes"
    if language == "en":
        days_desc = f"{abs(days_until_due)} days late" if is_overdue else f"{days_until_due} days remaining"

    # Try LLM generation if client is available
    if ai_client:
        if language == "es":
            sys_prompt = (
                f"Eres un asistente bancario enfocado en la prevención proactiva del sobreendeudamiento. "
                f"Escribe un mensaje breve (menos de 50 palabras), empático y sin juicio moral para {customer.full_name}. "
                f"Contexto: cuota de ${amount_due:.2f} con vencimiento el {due_date_str} ({days_desc}). "
                f"Historial: racha de {streak} pagos pendientes. Indicador de dificultad económica: {hardship}. "
                f"Reglas estrictas e inviolables de cumplimiento: "
                f"- Jamás amenaces con demandas, juicios, abogados de cobranza o acciones legales. "
                f"- Jamás amenaces con afectar el buró de crédito, manchar historial o listas negras. "
                f"- Jamás amenaces con embargos, retención de sueldo o visitas domiciliarias. "
                f"- Jamás avergüences al cliente ni uses términos como moroso o mala paga. "
                f"- No hagas promesas o garantías no autorizadas de quita o condonación. "
                f"- Si el cliente presenta dificultades, prioriza ofrecer alternativas flexibles y apoyo humano."
            )
        else:
            sys_prompt = (
                f"You are a payment reminder assistant for a bank. Write a short (under 50 words), "
                f"warm, supportive, and non-judgmental chat message to {customer.full_name} in English. "
                f"Context: installment of ${amount_due:.2f} due on {due_date_str} ({days_desc}). "
                f"Missed streak: {streak}. Hardship flag: {hardship}. "
                f"Hard rules: Never threaten legal action, wage garnishment, asset seizure, or damage to credit score/credit bureaus. "
                f"Never shame or insult the customer. Never promise unauthorized discounts or debt forgiveness. "
                f"Offer support, a flexible payment plan, or speaking with a specialist. "
                f"If hardship is true, do not pressure for payment; prioritize offering help and human connection."
            )
        try:
            res = await ai_client.messages.create(
                model="deepseek-chat",
                max_tokens=150,
                system=sys_prompt,
                messages=[{"role": "user", "content": "Please generate the reminder message."}],
            )
            candidate_text = res.content[0].text.strip()
            if candidate_text and not output_violates_guardrails(candidate_text):
                return candidate_text
        except Exception:
            pass

    # Template fallback
    if language == "es":
        if hardship:
            return (
                f"Hola {customer.full_name}, sabemos que se pueden presentar situaciones imprevistas. "
                f"Queremos recordarte que tienes una cuota de ${amount_due:.2f} pendiente, pero lo más importante es apoyarte. "
                f"¿Deseas que te conectemos con un especialista para evaluar opciones flexibles?"
            )
        elif is_overdue:
            return (
                f"Hola {customer.full_name}, notamos que tu cuota de ${amount_due:.2f} con vencimiento el {due_date_str} "
                f"se encuentra pendiente. Estamos a tu disposición para coordinar una alternativa de pago cómoda para ti."
            )
        else:
            return (
                f"Hola {customer.full_name}, te enviamos un cordial recordatorio de que tu próximo pago de ${amount_due:.2f} "
                f"vencerá el {due_date_str}. Si deseas programar el abono o revisar tus fechas de pago, con gusto te asistimos."
            )
    else:
        if hardship:
            return (
                f"Hi {customer.full_name}, we understand unexpected circumstances arise. "
                f"We wanted to reach out regarding your installment of ${amount_due:.2f}. "
                f"We are here to support you with flexible options or connect you with a specialist whenever you're ready."
            )
        elif is_overdue:
            return (
                f"Hi {customer.full_name}, we noticed your installment of ${amount_due:.2f} due on {due_date_str} "
                f"is currently unpaid. We are here to help you get back on track with a flexible arrangement."
            )
        else:
            return (
                f"Hi {customer.full_name}, friendly reminder that your upcoming installment of ${amount_due:.2f} "
                f"is scheduled for {due_date_str}. If you'd like to adjust your schedule or review payment options, we're here to help."
            )


async def generate_customer_chat_reply(
    db: Session,
    customer: models.Customer | None,
    convo: models.Conversation,
    user_message: str,
) -> str:
    """Generate a supportive, compliant response from the payment assistant to a customer's message."""
    # Detect language: if English keywords found, respond in English, otherwise default to Spanish
    lang = "es"
    if re.search(r"\b(hello|hi|help|due|payment|reschedule|can i|thank|how much)\b", user_message.lower()):
        lang = "en"

    payment = None
    hardship = False
    streak = 0
    cust_name = customer.full_name if customer else "Cliente"

    if customer:
        payment = (
            db.query(models.Payment)
            .join(models.Account)
            .filter(models.Account.customer_id == customer.id)
            .filter(models.Payment.payment_date.is_(None))
            .order_by(models.Payment.due_date.asc())
            .first()
        )
        risk = (
            db.query(models.RiskFeature)
            .filter_by(customer_id=customer.id)
            .order_by(models.RiskFeature.as_of_date.desc())
            .first()
        )
        act = (
            db.query(models.AccountActivity)
            .filter_by(customer_id=customer.id)
            .order_by(models.AccountActivity.snapshot_date.desc())
            .first()
        )
        hardship = act.hardship_flag if act else False
        streak = risk.missed_payment_streak if risk else 0

    amount_str = f"${float(payment.amount_due):.2f}" if payment else "pendiente"
    due_str = payment.due_date.strftime("%d/%m/%Y") if payment else "próximo"

    if ai_client:
        if lang == "es":
            sys_prompt = (
                f"Eres el asistente bancario de apoyo y prevención de endeudamiento de Boreal Bank. "
                f"Estás respondiendo a un mensaje de chat de {cust_name}. "
                f"Contexto: cuota de {amount_str} con vencimiento el {due_str}. "
                f"Reglas estrictas e inviolables de cumplimiento: "
                f"- Escribe en español un mensaje breve (menos de 60 palabras), cálido, empático y orientado a soluciones. "
                f"- Jamás amenaces con demandas, juicios, embargos, cobradores ni buró de crédito. "
                f"- Jamás juzgues ni avergüences al cliente. "
                f"- Si el cliente pregunta cómo pagar, reprogramar o resolver su situación, ofrece opciones concretas "
                f"(pago en parcialidades, extensión de fecha o contactar a un especialista financiero). "
                f"- Termina con una pregunta o siguiente paso sencillo y de apoyo."
            )
        else:
            sys_prompt = (
                f"You are the supportive debt-prevention assistant for Boreal Bank. "
                f"You are responding to a chat message from {cust_name}. "
                f"Context: installment of {amount_str} due on {due_str}. "
                f"Strict compliance rules: "
                f"- Write a short (under 60 words), warm, supportive, and solution-oriented reply in English. "
                f"- Never threaten legal action, wage garnishment, asset seizure, or credit bureau damage. "
                f"- Never judge or shame the customer. "
                f"- If the customer asks how to pay, reschedule, or resolve their debt, offer flexible alternatives "
                f"(split payments, date extension, or connecting with a specialist). "
                f"- End with a concrete, low-friction next step."
            )

        # Build recent message turns for conversational context
        turns = []
        for m in convo.messages[-6:]:
            role = "user" if m.role == models.MessageRole.USER else "assistant"
            turns.append({"role": role, "content": m.content})

        if not turns or turns[-1]["content"] != user_message:
            turns.append({"role": "user", "content": user_message})

        try:
            res = await ai_client.messages.create(
                model="deepseek-chat",
                max_tokens=150,
                system=sys_prompt,
                messages=turns,
            )
            candidate = res.content[0].text.strip()
            if candidate and not output_violates_guardrails(candidate):
                return candidate
        except Exception as e:
            print(f"Error calling LLM for customer chat: {e}")

    # Fallback response
    if lang == "es":
        return (
            f"Hola {cust_name}, con gusto te orientamos. Para tu cuota de {amount_str}, "
            f"podemos explorar alternativas como un pago parcial o una prórroga de fecha. "
            f"¿Deseas que coordinemos una opción flexible o prefieres hablar con un asesor especializado?"
        )
    else:
        return (
            f"Hello {cust_name}, we are happy to help. For your installment of {amount_str}, "
            f"we can look into a partial payment arrangement or extending the due date. "
            f"Would you like to review flexible options or speak with a specialist?"
        )


def get_risk_reminder_candidates(db: Session) -> list[dict[str, Any]]:
    """Query customers exceeding risk thresholds who have pending installments."""
    today = date.today()
    candidates = []

    risk_features = (
        db.query(models.RiskFeature)
        .order_by(models.RiskFeature.as_of_date.desc())
        .all()
    )
    latest_risks: dict[str, models.RiskFeature] = {}
    for rf in risk_features:
        if rf.customer_id not in latest_risks:
            latest_risks[rf.customer_id] = rf

    for customer_id, rf in latest_risks.items():
        is_risky = (
            rf.early_warning_flag
            or (rf.missed_payment_streak and rf.missed_payment_streak >= 1)
            or (rf.balance_trend_30d is not None and rf.balance_trend_30d <= -20.0)
            or (rf.consecutive_partial_payments and rf.consecutive_partial_payments >= 2)
        )
        if not is_risky:
            continue

        customer = db.get(models.Customer, customer_id)
        if not customer:
            continue

        next_payment = (
            db.query(models.Payment)
            .join(models.Account)
            .filter(models.Account.customer_id == customer_id)
            .filter(models.Payment.payment_date.is_(None))
            .order_by(models.Payment.due_date.asc())
            .first()
        )
        if not next_payment:
            continue

        latest_act = (
            db.query(models.AccountActivity)
            .filter_by(customer_id=customer_id)
            .order_by(models.AccountActivity.snapshot_date.desc())
            .first()
        )
        hardship = latest_act.hardship_flag if latest_act else False
        days_until_due = (next_payment.due_date - today).days

        last_assistant_msg = (
            db.query(models.Message)
            .join(models.Conversation)
            .filter(models.Conversation.customer_id == customer_id)
            .filter(models.Message.role == models.MessageRole.ASSISTANT)
            .order_by(models.Message.created_at.desc())
            .first()
        )

        candidates.append({
            "customer_id": customer.id,
            "customer_name": customer.full_name,
            "customer_email": customer.email,
            "early_warning_flag": rf.early_warning_flag,
            "missed_payment_streak": rf.missed_payment_streak,
            "consecutive_partial_payments": rf.consecutive_partial_payments,
            "balance_trend_30d": float(rf.balance_trend_30d) if rf.balance_trend_30d is not None else None,
            "hardship_flag": hardship,
            "payment_id": next_payment.id,
            "amount_due": float(next_payment.amount_due),
            "due_date": next_payment.due_date.isoformat(),
            "days_until_due": days_until_due,
            "is_overdue": days_until_due < 0,
            "last_reminder_at": last_assistant_msg.created_at.isoformat() if last_assistant_msg else None,
        })

    # Order candidates: overdue first, then by earliest due date
    candidates.sort(key=lambda c: (not c["is_overdue"], c["days_until_due"]))
    return candidates


@app.websocket("/ws/chat/{room_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    room_id: str,
    sender_name: str = Query("User", description="Display name of the participant"),
):
    """WebSocket endpoint supporting real-time chat partitioned into rooms.
    When room_id is a customer_id, it is backed by an active persistent Conversation in the DB.
    """
    initial_history = []
    is_customer_room = False
    customer_name = None

    db = SessionLocal()
    try:
        customer = db.get(models.Customer, room_id)
        if customer:
            is_customer_room = True
            customer_name = customer.full_name
            convo = get_or_create_active_conversation(db, customer.id)
            for m in convo.messages:
                name = "You" if m.role == models.MessageRole.USER else "Payment Assistant"
                initial_history.append({
                    "id": m.id,
                    "room_id": room_id,
                    "sender_name": name,
                    "text": m.content,
                    "type": "message",
                    "timestamp": m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
                })
    finally:
        db.close()

    await chat_manager.connect(
        websocket, room_id, sender_name, initial_history=initial_history if initial_history else None
    )
    try:
        while True:
            data = await websocket.receive_text()
            # Support both raw text or JSON payloads with sender_name & text
            try:
                parsed = json.loads(data)
                text = parsed.get("text", "")
                msg_sender = parsed.get("sender_name", sender_name)
            except Exception:
                text = data
                msg_sender = sender_name

            cleaned_text = text.strip()
            if cleaned_text:
                escalation_msg = None
                if is_customer_room:
                    # Persist message to DB Conversation
                    db = SessionLocal()
                    try:
                        active_convo = get_or_create_active_conversation(db, room_id)
                        is_customer_msg = (
                            msg_sender.lower() in ("you", "user", "customer") or msg_sender == customer_name
                        )
                        role = (
                            models.MessageRole.USER
                            if is_customer_msg
                            else models.MessageRole.ASSISTANT
                        )
                        is_distressed = False
                        distress_cats: list[str] = []
                        if is_customer_msg:
                            is_distressed, distress_cats = detect_customer_distress(cleaned_text)

                        db_msg = models.Message(
                            conversation_id=active_convo.id,
                            role=role,
                            content=cleaned_text,
                            created_at=datetime.utcnow(),
                            was_flagged=is_distressed,
                        )
                        db.add(db_msg)

                        if is_distressed:
                            active_convo.is_escalated = True
                            active_convo.escalated_at = datetime.utcnow()
                            active_convo.escalation_reason = f"Distress detected in categories: {', '.join(distress_cats)}"
                            record_conversation_event(
                                db=db,
                                conversation_id=active_convo.id,
                                event_type=models.ConversationEventType.CUSTOMER_DISTRESS_DETECTED,
                                title="Customer Distress Detected",
                                description=f"Customer expressed financial distress/hardship ({', '.join(distress_cats)}).",
                                metadata={
                                    "categories": distress_cats,
                                    "trigger_snippet": cleaned_text[:200],
                                },
                            )
                            record_conversation_event(
                                db=db,
                                conversation_id=active_convo.id,
                                event_type=models.ConversationEventType.CONVERSATION_ESCALATED,
                                title="Conversation Escalated to Human Specialist",
                                description="Automated AI debt-prevention paused; customer routed to human hardship specialist.",
                                metadata={"reason": active_convo.escalation_reason},
                            )

                        active_convo.last_message_at = datetime.utcnow()
                        db.commit()

                        # If distress detected, trigger immediate empathetic handoff message
                        if is_distressed:
                            lang = "es"
                            if re.search(r"\b(job|money|afford|hospital|evict|funeral|laid off)\b", cleaned_text.lower()):
                                lang = "en"
                            reply_text = get_escalation_reply(lang)
                            asst_db_msg = models.Message(
                                conversation_id=active_convo.id,
                                role=models.MessageRole.ASSISTANT,
                                content=reply_text,
                                created_at=datetime.utcnow(),
                                was_flagged=False,
                            )
                            db.add(asst_db_msg)
                            active_convo.last_message_at = datetime.utcnow()
                            db.commit()
                            escalation_msg = reply_text

                            record_conversation_event(
                                db=db,
                                conversation_id=active_convo.id,
                                event_type=models.ConversationEventType.SPECIALIST_HANDOFF,
                                title="Specialist Handoff Notice Dispatched",
                                description="Empathetic handoff message delivered to customer confirming human team referral.",
                                metadata={"language": lang},
                            )

                        elif is_customer_msg:
                            # Generate conversational reply from AI assistant
                            reply_text = await generate_customer_chat_reply(
                                db=db,
                                customer=customer,
                                convo=active_convo,
                                user_message=cleaned_text,
                            )
                            asst_db_msg = models.Message(
                                conversation_id=active_convo.id,
                                role=models.MessageRole.ASSISTANT,
                                content=reply_text,
                                created_at=datetime.utcnow(),
                                was_flagged=False,
                            )
                            db.add(asst_db_msg)
                            active_convo.last_message_at = datetime.utcnow()
                            db.commit()
                            escalation_msg = reply_text
                    finally:
                        db.close()

                msg = chat_manager.format_message(
                    room_id=room_id,
                    sender_name=msg_sender,
                    text=cleaned_text,
                    msg_type="message",
                )
                await chat_manager.broadcast(room_id, msg)

                if escalation_msg:
                    asst_ws_msg = chat_manager.format_message(
                        room_id=room_id,
                        sender_name="Payment Assistant",
                        text=escalation_msg,
                        msg_type="message",
                    )
                    await chat_manager.broadcast(room_id, asst_ws_msg)
    except WebSocketDisconnect:
        await chat_manager.disconnect(websocket, room_id)


@app.get("/chat/rooms", tags=["Chat"])
def list_chat_rooms():
    """List currently active chat rooms, participant count, and message count."""
    return chat_manager.get_active_rooms()


@app.get("/chat/rooms/{room_id}/messages", tags=["Chat"])
def get_room_messages(room_id: str):
    """Retrieve recent message history for a given chat room."""
    return chat_manager.get_history(room_id)


@app.post("/chat/rooms/{room_id}/messages", status_code=status.HTTP_201_CREATED, tags=["Chat"])
async def post_room_message(room_id: str, payload: schemas.ChatMessagePayload):
    """Inject a message into a chat room via REST (e.g. from an automated bot,
    debt prevention alert, or payment reminder) and broadcast to connected WebSockets.
    """
    cleaned_text = payload.text.strip()
    if payload.sender_name.lower() not in ("you", "user", "customer"):
        try:
            validate_compliance_or_raise(cleaned_text, context="Outgoing message")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    msg = chat_manager.format_message(
        room_id=room_id,
        sender_name=payload.sender_name,
        text=cleaned_text,
        msg_type="message",
    )
    await chat_manager.broadcast(room_id, msg)
    return msg


@app.get("/conversations", tags=["Chat"])
@app.get("/chat/conversations", tags=["Chat"])
def list_conversations(
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
):
    """List all existing conversations with latest activity and customer details."""
    query = (
        select(models.Conversation)
        .options(
            joinedload(models.Conversation.customer),
            selectinload(models.Conversation.messages),
            selectinload(models.Conversation.events),
        )
        .order_by(models.Conversation.last_message_at.desc())
    )
    if customer_id:
        query = query.filter(models.Conversation.customer_id == customer_id)
    conversations = db.execute(query).scalars().all()
    result = []
    for c in conversations:
        last_msg = c.messages[-1].content if c.messages else None
        result.append({
            "id": c.id,
            "customer_id": c.customer_id,
            "customer_name": c.customer.full_name if c.customer else "Unknown Customer",
            "customer_email": c.customer.email if c.customer else None,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "channel": c.channel.value if c.channel else "app",
            "is_escalated": c.is_escalated,
            "escalated_at": c.escalated_at.isoformat() if c.escalated_at else None,
            "escalation_reason": c.escalation_reason,
            "message_count": len(c.messages),
            "event_count": len(c.events) if c.events else 0,
            "last_message": last_msg,
        })
    return result


@app.get("/conversations/{conversation_id}/messages", tags=["Chat"])
@app.get("/chat/conversations/{conversation_id}/messages", tags=["Chat"])
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve all messages belonging to a conversation."""
    convo = db.get(models.Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role.value,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "flagged": m.was_flagged,
        }
        for m in convo.messages
    ]


@app.get("/conversations/{conversation_id}/events", tags=["Chat"])
@app.get("/chat/conversations/{conversation_id}/events", tags=["Chat"])
def get_conversation_events(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve all compliance and audit milestone events for a conversation.
    Dedicated regulatory audit trail decoupled from dialogue turns and LLM context.
    """
    convo = db.get(models.Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    events = (
        db.query(models.ConversationEvent)
        .filter_by(conversation_id=conversation_id)
        .order_by(models.ConversationEvent.created_at.asc())
        .all()
    )
    return [
        {
            "id": e.id,
            "conversation_id": e.conversation_id,
            "event_type": e.event_type.value,
            "title": e.title,
            "description": e.description,
            "metadata": json.loads(e.metadata_json) if e.metadata_json else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]



@app.get("/risk-reminders/candidates", tags=["Chat"])
@app.get("/chat/risk-reminders/candidates", tags=["Chat"])
def get_candidates_for_risk_reminders(db: Session = Depends(get_db)):
    """List all customers beyond the risk threshold with unpaid installments who qualify for an AI reminder."""
    return get_risk_reminder_candidates(db)


@app.post("/risk-reminders/send", status_code=status.HTTP_201_CREATED, tags=["Chat"])
@app.post("/chat/risk-reminders/send", status_code=status.HTTP_201_CREATED, tags=["Chat"])
async def send_risk_reminder(payload: schemas.SendRiskReminderPayload, db: Session = Depends(get_db)):
    """Generate, persist, and broadcast an AI debt-prevention reminder to an at-risk customer."""
    customer = db.get(models.Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Fetch earliest pending payment
    payment = (
        db.query(models.Payment)
        .join(models.Account)
        .filter(models.Account.customer_id == customer.id)
        .filter(models.Payment.payment_date.is_(None))
        .order_by(models.Payment.due_date.asc())
        .first()
    )
    if not payment:
        raise HTTPException(status_code=400, detail="Customer has no active unpaid installments")

    risk = (
        db.query(models.RiskFeature)
        .filter_by(customer_id=customer.id)
        .order_by(models.RiskFeature.as_of_date.desc())
        .first()
    )
    activity = (
        db.query(models.AccountActivity)
        .filter_by(customer_id=customer.id)
        .order_by(models.AccountActivity.snapshot_date.desc())
        .first()
    )

    if payload.custom_message and payload.custom_message.strip():
        reminder_text = payload.custom_message.strip()
        try:
            validate_compliance_or_raise(reminder_text, context="Custom reminder message")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        reminder_text = await generate_risk_reminder(
            customer=customer,
            payment=payment,
            risk=risk,
            activity=activity,
            language=payload.language or "es",
        )

    violation = output_violates_guardrails(reminder_text)
    was_flagged = violation is not None

    # Resolve or create active conversation
    convo = get_or_create_active_conversation(db, customer.id)
    if activity and activity.hardship_flag:
        convo.is_escalated = True
        convo.escalated_at = datetime.utcnow()
        convo.escalation_reason = "Customer hardship flag present in account activity"
        record_conversation_event(
            db=db,
            conversation_id=convo.id,
            event_type=models.ConversationEventType.CONVERSATION_ESCALATED,
            title="Conversation Escalated to Specialist",
            description="Conversation marked for specialist review due to active hardship flag.",
            metadata={"source": "account_activity", "hardship_flag": True},
        )

    # Persist message
    db_msg = models.Message(
        conversation_id=convo.id,
        role=models.MessageRole.ASSISTANT,
        content=reminder_text,
        created_at=datetime.utcnow(),
        was_flagged=was_flagged,
    )
    db.add(db_msg)
    convo.last_message_at = datetime.utcnow()
    db.commit()
    db.refresh(db_msg)

    # Record compliance audit milestone
    record_conversation_event(
        db=db,
        conversation_id=convo.id,
        event_type=models.ConversationEventType.RISK_REMINDER_TRIGGERED,
        title="Proactive AI Risk Reminder Dispatched",
        description=f"Automated risk reminder sent to {customer.full_name} for pending installment.",
        metadata={
            "customer_id": customer.id,
            "payment_id": payment.id,
            "amount_due": float(payment.amount_due),
            "due_date": payment.due_date.isoformat(),
            "was_flagged": was_flagged,
            "language": payload.language or "es",
        },
    )

    if was_flagged:
        record_conversation_event(
            db=db,
            conversation_id=convo.id,
            event_type=models.ConversationEventType.GUARDRAIL_VIOLATION_BLOCKED,
            title="Guardrail Flagged Output",
            description=f"Automated reminder flagged by internal guardrail: {violation}",
            metadata={"violation": violation},
        )


    # Broadcast to customer's WebSocket room
    ws_msg = chat_manager.format_message(
        room_id=customer.id,
        sender_name="Payment Assistant",
        text=reminder_text,
        msg_type="message",
    )
    await chat_manager.broadcast(customer.id, ws_msg)

    return {
        "success": True,
        "conversation_id": convo.id,
        "customer_id": customer.id,
        "message": {
            "id": db_msg.id,
            "role": db_msg.role.value,
            "content": db_msg.content,
            "created_at": db_msg.created_at.isoformat() if db_msg.created_at else None,
            "flagged": db_msg.was_flagged,
        },
    }


@app.get("/chat/{room_id}", response_class=HTMLResponse, tags=["Chat"])
def chat_room_page(room_id: str):
    """Renders a WhatsApp-styled web interface to simulate chatting with individuals."""
    html_path = os.path.join(os.path.dirname(__file__), "chat_ui.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content.replace("{{ room_id }}", room_id))