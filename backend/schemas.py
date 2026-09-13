from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from models import (
    Channel,
    EmploymentStatus,
    PaymentMethod,
    PaymentStatus,
    ProductType,
)


class CustomerCreate(BaseModel):
    full_name: str
    email: str
    age: int | None = None
    region: str | None = None
    employment_status: EmploymentStatus | None = None
    income_bracket: str | None = None
    tenure_months: int | None = None
    credit_score: int | None = None


class CustomerOut(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class AccountCreate(BaseModel):
    customer_id: str
    product_type: ProductType
    principal_amount: float
    interest_rate: float
    total_installments: int | None = None


class AccountOut(AccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    opened_at: datetime
    is_active: bool


class PaymentCreate(BaseModel):
    account_id: str
    amount_due: float
    amount_paid: float | None = None
    due_date: date
    payment_date: date | None = None
    status: PaymentStatus = PaymentStatus.ON_TIME
    days_late: int = 0
    payment_method: PaymentMethod | None = None
    channel: Channel | None = None
    is_partial_payment: bool = False
    installment_number: int | None = None


class PaymentOut(PaymentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    outstanding_balance_after: float | None = None
    late_fee_charged: float | None = None
    retry_count: int


class AccountActivityCreate(BaseModel):
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


class RiskFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    customer_id: str
    as_of_date: date
    consecutive_partial_payments: int
    missed_payment_streak: int
    avg_days_late_90d: float
    early_warning_flag: bool
    defaulted: bool
    days_to_default: int | None = None