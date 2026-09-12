"""
SQLAlchemy models for a debt-prevention simulation system.

Structure:
    Customer -> Account/Loan -> Payment (transactional, one row per due payment)
    Customer -> AccountActivity (balances, logins, behavioral signals)
    Customer -> RiskFeature (derived features feeding the prediction model)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def gen_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProductType(str, enum.Enum):
    MORTGAGE = "mortgage"
    PERSONAL_LOAN = "personal_loan"
    CREDIT_CARD = "credit_card"
    AUTO_LOAN = "auto_loan"


class PaymentStatus(str, enum.Enum):
    ON_TIME = "on_time"
    LATE = "late"
    PARTIAL = "partial"
    MISSED = "missed"
    REVERSED = "reversed"
    GRACE_PERIOD = "grace_period"


class PaymentMethod(str, enum.Enum):
    AUTO_DEBIT = "auto_debit"
    TRANSFER = "transfer"
    CASH = "cash"
    CARD = "card"
    THIRD_PARTY = "third_party"


class Channel(str, enum.Enum):
    APP = "app"
    BRANCH = "branch"
    ATM = "atm"
    CALL_CENTER = "call_center"
    WEB = "web"


class EmploymentStatus(str, enum.Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    employment_status: Mapped[EmploymentStatus | None] = mapped_column(
        Enum(EmploymentStatus), nullable=True
    )
    income_bracket: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tenure_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    accounts: Mapped[list["Account"]] = relationship(back_populates="customer")
    activities: Mapped[list["AccountActivity"]] = relationship(back_populates="customer")
    risk_features: Mapped[list["RiskFeature"]] = relationship(back_populates="customer")


# ---------------------------------------------------------------------------
# Account / Loan
# ---------------------------------------------------------------------------

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType))
    principal_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    interest_rate: Mapped[float] = mapped_column(Numeric(5, 4))
    total_installments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    customer: Mapped["Customer"] = relationship(back_populates="accounts")
    payments: Mapped[list["Payment"]] = relationship(back_populates="account")


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))

    amount_due: Mapped[float] = mapped_column(Numeric(12, 2))
    amount_paid: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    minimum_payment_due: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    outstanding_balance_after: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    late_fee_charged: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    interest_accrued: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    due_date: Mapped[Date] = mapped_column(Date)
    payment_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    posted_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    billing_cycle_start: Mapped[Date | None] = mapped_column(Date, nullable=True)
    billing_cycle_end: Mapped[Date | None] = mapped_column(Date, nullable=True)

    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.ON_TIME)
    days_late: Mapped[int] = mapped_column(Integer, default=0)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod), nullable=True)
    channel: Mapped[Channel | None] = mapped_column(Enum(Channel), nullable=True)
    is_partial_payment: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    installment_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    account: Mapped["Account"] = relationship(back_populates="payments")


# ---------------------------------------------------------------------------
# Account activity (behavioral / early-warning signals)
# ---------------------------------------------------------------------------

class AccountActivity(Base):
    __tablename__ = "account_activity"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    snapshot_date: Mapped[Date] = mapped_column(Date)

    checking_balance: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    savings_balance: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    overdraft_count_30d: Mapped[int] = mapped_column(Integer, default=0)
    large_withdrawal_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_deposit_detected: Mapped[bool] = mapped_column(Boolean, default=True)
    app_logins_30d: Mapped[int] = mapped_column(Integer, default=0)
    support_contacts_30d: Mapped[int] = mapped_column(Integer, default=0)
    hardship_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    customer: Mapped["Customer"] = relationship(back_populates="activities")


# ---------------------------------------------------------------------------
# Derived risk features (feeds the prevention model)
# ---------------------------------------------------------------------------

class RiskFeature(Base):
    __tablename__ = "risk_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    as_of_date: Mapped[Date] = mapped_column(Date)

    consecutive_partial_payments: Mapped[int] = mapped_column(Integer, default=0)
    missed_payment_streak: Mapped[int] = mapped_column(Integer, default=0)
    avg_days_late_90d: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    debt_to_income_ratio: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    credit_utilization_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    balance_trend_30d: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)  # % change
    early_warning_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    # labels for supervised learning
    defaulted: Mapped[bool] = mapped_column(Boolean, default=False)
    days_to_default: Mapped[int | None] = mapped_column(Integer, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="risk_features")
