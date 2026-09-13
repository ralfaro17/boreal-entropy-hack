from datetime import date, datetime

from models import (
    Channel,
    EmploymentStatus,
    PaymentMethod,
    PaymentStatus,
    ProductType,
)
from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Customer Schemas
# ---------------------------------------------------------------------------

class CustomerBase(BaseModel):
    full_name: str
    email: str
    age: int | None = None
    region: str | None = None
    employment_status: EmploymentStatus | None = None
    income_bracket: str | None = None
    tenure_months: int | None = None
    credit_score: int | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    age: int | None = None
    region: str | None = None
    employment_status: EmploymentStatus | None = None
    income_bracket: str | None = None
    tenure_months: int | None = None
    credit_score: int | None = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Account Schemas
# ---------------------------------------------------------------------------

class AccountBase(BaseModel):
    customer_id: str
    product_type: ProductType
    principal_amount: float
    interest_rate: float
    total_installments: int | None = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    product_type: ProductType | None = None
    principal_amount: float | None = None
    interest_rate: float | None = None
    total_installments: int | None = None
    is_active: bool | None = None


class AccountOut(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    opened_at: datetime
    is_active: bool


# ---------------------------------------------------------------------------
# Payment Schemas
# ---------------------------------------------------------------------------

class PaymentBase(BaseModel):
    account_id: str
    amount_due: float
    amount_paid: float | None = None
    currency: str = "USD"
    minimum_payment_due: float | None = None
    due_date: date
    payment_date: date | None = None
    posted_date: date | None = None
    billing_cycle_start: date | None = None
    billing_cycle_end: date | None = None
    status: PaymentStatus = PaymentStatus.ON_TIME
    days_late: int = 0
    payment_method: PaymentMethod | None = None
    channel: Channel | None = None
    is_partial_payment: bool = False
    installment_number: int | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount_due: float | None = None
    amount_paid: float | None = None
    currency: str | None = None
    minimum_payment_due: float | None = None
    outstanding_balance_after: float | None = None
    late_fee_charged: float | None = None
    interest_accrued: float | None = None
    due_date: date | None = None
    payment_date: date | None = None
    posted_date: date | None = None
    billing_cycle_start: date | None = None
    billing_cycle_end: date | None = None
    status: PaymentStatus | None = None
    days_late: int | None = None
    payment_method: PaymentMethod | None = None
    channel: Channel | None = None
    is_partial_payment: bool | None = None
    retry_count: int | None = None
    installment_number: int | None = None


class PaymentOut(PaymentBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    outstanding_balance_after: float | None = None
    late_fee_charged: float | None = None
    interest_accrued: float | None = None
    retry_count: int = 0


# ---------------------------------------------------------------------------
# Account Activity Schemas
# ---------------------------------------------------------------------------

class AccountActivityBase(BaseModel):
    customer_id: str
    snapshot_date: date
    checking_balance: float | None = None
    savings_balance: float | None = None
    overdraft_count_30d: int = 0
    large_withdrawal_flag: bool = False
    salary_deposit_detected: bool = True
    app_logins_30d: int = 0
    support_contacts_30d: int = 0
    hardship_flag: bool = False


class AccountActivityCreate(AccountActivityBase):
    pass


class AccountActivityUpdate(BaseModel):
    snapshot_date: date | None = None
    checking_balance: float | None = None
    savings_balance: float | None = None
    overdraft_count_30d: int | None = None
    large_withdrawal_flag: bool | None = None
    salary_deposit_detected: bool | None = None
    app_logins_30d: int | None = None
    support_contacts_30d: int | None = None
    hardship_flag: bool | None = None


class AccountActivityOut(AccountActivityBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Risk Feature Schemas
# ---------------------------------------------------------------------------

class RiskFeatureBase(BaseModel):
    customer_id: str
    as_of_date: date
    consecutive_partial_payments: int = 0
    missed_payment_streak: int = 0
    avg_days_late_90d: float = 0.0
    debt_to_income_ratio: float | None = None
    credit_utilization_pct: float | None = None
    balance_trend_30d: float | None = None
    early_warning_flag: bool = False
    defaulted: bool = False
    days_to_default: int | None = None


class RiskFeatureCreate(RiskFeatureBase):
    pass


class RiskFeatureUpdate(BaseModel):
    as_of_date: date | None = None
    consecutive_partial_payments: int | None = None
    missed_payment_streak: int | None = None
    avg_days_late_90d: float | None = None
    debt_to_income_ratio: float | None = None
    credit_utilization_pct: float | None = None
    balance_trend_30d: float | None = None
    early_warning_flag: bool | None = None
    defaulted: bool | None = None
    days_to_default: int | None = None


class RiskFeatureOut(RiskFeatureBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Chat Schemas
# ---------------------------------------------------------------------------

class ChatMessagePayload(BaseModel):
    sender_name: str = "Bank Bot"
    text: str


class SendRiskReminderPayload(BaseModel):
    customer_id: str
    language: str = "es"
    custom_message: str | None = None