import json
import os
from contextlib import asynccontextmanager
from typing import Any

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
from sqlalchemy.orm import Session

import models
import schemas
from chat import chat_manager
from database import check_db_connection, get_db, init_db


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
# WebSocket & WhatsApp-Style Chat Rooms
# ===========================================================================

@app.websocket("/ws/chat/{room_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    room_id: str,
    sender_name: str = Query("User", description="Display name of the participant"),
):
    """WebSocket endpoint supporting real-time chat partitioned into rooms.

    Simulates WhatsApp conversations with participants.
    """
    await chat_manager.connect(websocket, room_id, sender_name)
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

            if text.strip():
                msg = chat_manager.format_message(
                    room_id=room_id,
                    sender_name=msg_sender,
                    text=text.strip(),
                    msg_type="message",
                )
                await chat_manager.broadcast(room_id, msg)
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
    msg = chat_manager.format_message(
        room_id=room_id,
        sender_name=payload.sender_name,
        text=payload.text,
        msg_type="message",
    )
    await chat_manager.broadcast(room_id, msg)
    return msg


@app.get("/chat/{room_id}", response_class=HTMLResponse, tags=["Chat"])
def chat_room_page(room_id: str):
    """Renders a WhatsApp-styled web interface to simulate chatting with individuals."""
    html_path = os.path.join(os.path.dirname(__file__), "chat_ui.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content.replace("{{ room_id }}", room_id))