"""
Demo mock data generator for Boreal Entropy.

Generates 10 structured personas showcasing all risk engine branching logic:
1. Sarah Steady - Healthy Baseline 1 (on-time payments, steady checking & savings)
2. Marcus Model - Healthy Baseline 2 (mortgage, prime credit score, auto-debit)
3. David Depleting - Liquidity Depletion (balance drop >20% triggers early_warning_flag)
4. Patricia Partial - Consecutive Partial Payments (3 partials triggers early_warning_flag)
5. Michael Missed - Missed Payment Streak (2 missed payments triggers early_warning_flag)
6. Helen Hardship - Declared Hardship (hardship_flag=True, triggers human handoff tone)
7. Daniel Default - Imminent / Severe Default (3 missed + >90 days late -> defaulted=True)
8. Lucas Live - Distress Trigger for Live Demo (clean chat, ready for "I just lost my job")
9. Morgan Multi - Multi-Product Borrower (Personal Loan + Credit Card + Auto Loan)
10. Chloe Clean - Clean Slate / Blank (fresh account, zero conversations)
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import models

NAMESPACE = uuid.UUID("a3b8c2d1-e4f5-4678-90ab-cdef12345678")


def make_id(key: str) -> str:
    """Generate a deterministic UUID string based on a distinct key."""
    return str(uuid.uuid5(NAMESPACE, key))


def get_demo_dataset():
    today = date.today()
    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------------------------
    # 1. Customers (10 Personas)
    # ---------------------------------------------------------------------------
    customers = [
        # Persona 1: Healthy Baseline 1
        models.Customer(
            id=make_id("customer_sarah_steady"),
            full_name="Sarah Steady",
            email="sarah.steady@example.com",
            age=34,
            region="North",
            employment_status=models.EmploymentStatus.EMPLOYED,
            income_bracket="$75k-$100k",
            tenure_months=36,
            credit_score=760,
            created_at=now - timedelta(days=36 * 30),
        ),
        # Persona 2: Healthy Baseline 2
        models.Customer(
            id=make_id("customer_marcus_model"),
            full_name="Marcus Model",
            email="marcus.model@example.com",
            age=42,
            region="West",
            employment_status=models.EmploymentStatus.EMPLOYED,
            income_bracket="$100k-$150k",
            tenure_months=48,
            credit_score=810,
            created_at=now - timedelta(days=48 * 30),
        ),
        # Persona 3: Liquidity Depletion
        models.Customer(
            id=make_id("customer_david_depleting"),
            full_name="David Depleting",
            email="david.depleting@example.com",
            age=29,
            region="East",
            employment_status=models.EmploymentStatus.EMPLOYED,
            income_bracket="$50k-$75k",
            tenure_months=18,
            credit_score=675,
            created_at=now - timedelta(days=18 * 30),
        ),
        # Persona 4: Consecutive Partial Payments
        models.Customer(
            id=make_id("customer_patricia_partial"),
            full_name="Patricia Partial",
            email="patricia.partial@example.com",
            age=38,
            region="South",
            employment_status=models.EmploymentStatus.SELF_EMPLOYED,
            income_bracket="$40k-$60k",
            tenure_months=22,
            credit_score=630,
            created_at=now - timedelta(days=22 * 30),
        ),
        # Persona 5: Missed Payment Streak
        models.Customer(
            id=make_id("customer_michael_missed"),
            full_name="Michael Missed",
            email="michael.missed@example.com",
            age=45,
            region="Midwest",
            employment_status=models.EmploymentStatus.EMPLOYED,
            income_bracket="$60k-$80k",
            tenure_months=30,
            credit_score=610,
            created_at=now - timedelta(days=30 * 30),
        ),
        # Persona 6: Declared Hardship
        models.Customer(
            id=make_id("customer_helen_hardship"),
            full_name="Helen Hardship",
            email="helen.hardship@example.com",
            age=51,
            region="North",
            employment_status=models.EmploymentStatus.UNEMPLOYED,
            income_bracket="<$30k",
            tenure_months=14,
            credit_score=590,
            created_at=now - timedelta(days=14 * 30),
        ),
        # Persona 7: Imminent / Severe Default
        models.Customer(
            id=make_id("customer_daniel_default"),
            full_name="Daniel Default",
            email="daniel.default@example.com",
            age=36,
            region="Central",
            employment_status=models.EmploymentStatus.UNEMPLOYED,
            income_bracket="$30k-$50k",
            tenure_months=16,
            credit_score=520,
            created_at=now - timedelta(days=16 * 30),
        ),
        # Persona 8: Distress Trigger for Live Demo
        models.Customer(
            id=make_id("customer_lucas_live"),
            full_name="Lucas Live",
            email="lucas.live@example.com",
            age=31,
            region="West",
            employment_status=models.EmploymentStatus.EMPLOYED,
            income_bracket="$65k-$85k",
            tenure_months=20,
            credit_score=685,
            created_at=now - timedelta(days=20 * 30),
        ),
        # Persona 9: Multi-Product Borrower
        models.Customer(
            id=make_id("customer_morgan_multi"),
            full_name="Morgan Multi",
            email="morgan.multi@example.com",
            age=39,
            region="South",
            employment_status=models.EmploymentStatus.EMPLOYED,
            income_bracket="$90k-$120k",
            tenure_months=40,
            credit_score=735,
            created_at=now - timedelta(days=40 * 30),
        ),
        # Persona 10: Clean Slate / Blank
        models.Customer(
            id=make_id("customer_chloe_clean"),
            full_name="Chloe Clean",
            email="chloe.clean@example.com",
            age=26,
            region="North",
            employment_status=models.EmploymentStatus.EMPLOYED,
            income_bracket="$55k-$70k",
            tenure_months=8,
            credit_score=710,
            created_at=now - timedelta(days=8 * 30),
        ),
    ]

    # ---------------------------------------------------------------------------
    # 2. Accounts (12 Accounts across 10 customers)
    # ---------------------------------------------------------------------------
    accounts = [
        # Sarah Steady: Personal Loan ($12,000)
        models.Account(
            id=make_id("account_sarah"),
            customer_id=make_id("customer_sarah_steady"),
            product_type=models.ProductType.PERSONAL_LOAN,
            principal_amount=12000.00,
            interest_rate=0.0650,
            total_installments=36,
            opened_at=now - timedelta(days=180),
            is_active=True,
        ),
        # Marcus Model: Mortgage ($320,000)
        models.Account(
            id=make_id("account_marcus"),
            customer_id=make_id("customer_marcus_model"),
            product_type=models.ProductType.MORTGAGE,
            principal_amount=320000.00,
            interest_rate=0.0420,
            total_installments=360,
            opened_at=now - timedelta(days=365),
            is_active=True,
        ),
        # David Depleting: Personal Loan ($8,000)
        models.Account(
            id=make_id("account_david"),
            customer_id=make_id("customer_david_depleting"),
            product_type=models.ProductType.PERSONAL_LOAN,
            principal_amount=8000.00,
            interest_rate=0.0890,
            total_installments=24,
            opened_at=now - timedelta(days=150),
            is_active=True,
        ),
        # Patricia Partial: Credit Card ($4,500)
        models.Account(
            id=make_id("account_patricia"),
            customer_id=make_id("customer_patricia_partial"),
            product_type=models.ProductType.CREDIT_CARD,
            principal_amount=4500.00,
            interest_rate=0.1999,
            total_installments=None,
            opened_at=now - timedelta(days=240),
            is_active=True,
        ),
        # Michael Missed: Auto Loan ($18,000)
        models.Account(
            id=make_id("account_michael"),
            customer_id=make_id("customer_michael_missed"),
            product_type=models.ProductType.AUTO_LOAN,
            principal_amount=18000.00,
            interest_rate=0.0720,
            total_installments=48,
            opened_at=now - timedelta(days=300),
            is_active=True,
        ),
        # Helen Hardship: Personal Loan ($6,000)
        models.Account(
            id=make_id("account_helen"),
            customer_id=make_id("customer_helen_hardship"),
            product_type=models.ProductType.PERSONAL_LOAN,
            principal_amount=6000.00,
            interest_rate=0.0950,
            total_installments=24,
            opened_at=now - timedelta(days=180),
            is_active=True,
        ),
        # Daniel Default: Personal Loan ($10,000)
        models.Account(
            id=make_id("account_daniel"),
            customer_id=make_id("customer_daniel_default"),
            product_type=models.ProductType.PERSONAL_LOAN,
            principal_amount=10000.00,
            interest_rate=0.1250,
            total_installments=36,
            opened_at=now - timedelta(days=240),
            is_active=True,
        ),
        # Lucas Live: Personal Loan ($9,500)
        models.Account(
            id=make_id("account_lucas"),
            customer_id=make_id("customer_lucas_live"),
            product_type=models.ProductType.PERSONAL_LOAN,
            principal_amount=9500.00,
            interest_rate=0.0790,
            total_installments=24,
            opened_at=now - timedelta(days=180),
            is_active=True,
        ),
        # Morgan Multi: Account 1 - Personal Loan ($15,000)
        models.Account(
            id=make_id("account_morgan_loan"),
            customer_id=make_id("customer_morgan_multi"),
            product_type=models.ProductType.PERSONAL_LOAN,
            principal_amount=15000.00,
            interest_rate=0.0750,
            total_installments=36,
            opened_at=now - timedelta(days=240),
            is_active=True,
        ),
        # Morgan Multi: Account 2 - Credit Card ($6,000)
        models.Account(
            id=make_id("account_morgan_card"),
            customer_id=make_id("customer_morgan_multi"),
            product_type=models.ProductType.CREDIT_CARD,
            principal_amount=6000.00,
            interest_rate=0.1850,
            total_installments=None,
            opened_at=now - timedelta(days=400),
            is_active=True,
        ),
        # Morgan Multi: Account 3 - Auto Loan ($24,000)
        models.Account(
            id=make_id("account_morgan_auto"),
            customer_id=make_id("customer_morgan_multi"),
            product_type=models.ProductType.AUTO_LOAN,
            principal_amount=24000.00,
            interest_rate=0.0590,
            total_installments=60,
            opened_at=now - timedelta(days=120),
            is_active=True,
        ),
        # Chloe Clean: Personal Loan ($5,000)
        models.Account(
            id=make_id("account_chloe"),
            customer_id=make_id("customer_chloe_clean"),
            product_type=models.ProductType.PERSONAL_LOAN,
            principal_amount=5000.00,
            interest_rate=0.0820,
            total_installments=18,
            opened_at=now - timedelta(days=90),
            is_active=True,
        ),
    ]

    # ---------------------------------------------------------------------------
    # 3. Payments (~75 Payments)
    # ---------------------------------------------------------------------------
    payments = []

    # Helper to append past resolved payment
    def add_past_payment(
        acct_id: str,
        due_offset_days: int,
        amount_due: float,
        amount_paid: float | None,
        status: models.PaymentStatus,
        days_late: int = 0,
        is_partial: bool = False,
        retry_count: int = 0,
        pay_method=models.PaymentMethod.AUTO_DEBIT,
        channel=models.Channel.APP,
        installment_no: int | None = None,
        key_suffix: str = "",
    ):
        p_due = today - timedelta(days=due_offset_days)
        p_date = (p_due + timedelta(days=days_late)) if amount_paid is not None else None
        payments.append(
            models.Payment(
                id=make_id(f"pay_{acct_id}_{key_suffix}"),
                account_id=acct_id,
                amount_due=amount_due,
                amount_paid=amount_paid,
                currency="USD",
                minimum_payment_due=amount_due * 0.1 if amount_due else None,
                due_date=p_due,
                payment_date=p_date,
                posted_date=p_date,
                status=status,
                days_late=days_late,
                payment_method=pay_method if amount_paid else None,
                channel=channel if amount_paid else None,
                is_partial_payment=is_partial,
                retry_count=retry_count,
                installment_number=installment_no,
            )
        )

    # Helper to append upcoming unresolved payment
    def add_upcoming_payment(
        acct_id: str,
        due_in_days: int,
        amount_due: float,
        installment_no: int | None = None,
        key_suffix: str = "upcoming",
        status: models.PaymentStatus = models.PaymentStatus.ON_TIME,
    ):
        payments.append(
            models.Payment(
                id=make_id(f"pay_{acct_id}_{key_suffix}"),
                account_id=acct_id,
                amount_due=amount_due,
                amount_paid=None,
                currency="USD",
                minimum_payment_due=amount_due * 0.1,
                due_date=today + timedelta(days=due_in_days),
                payment_date=None,
                posted_date=None,
                status=status,
                days_late=0,
                is_partial_payment=False,
                retry_count=0,
                installment_number=installment_no,
            )
        )

    # 1. Sarah Steady: 5 on-time resolved + 1 upcoming due in 7 days
    for i, offset in enumerate([150, 120, 90, 60, 30], start=1):
        add_past_payment(
            make_id("account_sarah"),
            offset,
            367.82,
            367.82,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    add_upcoming_payment(make_id("account_sarah"), 7, 367.82, installment_no=6)

    # 2. Marcus Model: 6 on-time resolved + 1 upcoming due in 12 days
    for i, offset in enumerate([180, 150, 120, 90, 60, 30], start=1):
        add_past_payment(
            make_id("account_marcus"),
            offset,
            1564.90,
            1564.90,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    add_upcoming_payment(make_id("account_marcus"), 12, 1564.90, installment_no=7)

    # 3. David Depleting: 4 on-time resolved + 1 upcoming due in 5 days
    for i, offset in enumerate([120, 90, 60, 30], start=1):
        add_past_payment(
            make_id("account_david"),
            offset,
            365.12,
            365.12,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    add_upcoming_payment(make_id("account_david"), 5, 365.12, installment_no=5)

    # 4. Patricia Partial: 2 on-time + 3 consecutive PARTIAL resolved + 1 upcoming due in 4 days
    add_past_payment(
        make_id("account_patricia"),
        150,
        250.00,
        250.00,
        models.PaymentStatus.ON_TIME,
        installment_no=1,
        key_suffix="1",
    )
    add_past_payment(
        make_id("account_patricia"),
        120,
        250.00,
        250.00,
        models.PaymentStatus.ON_TIME,
        installment_no=2,
        key_suffix="2",
    )
    # 3 consecutive partial payments (due 90, 60, 30 days ago)
    add_past_payment(
        make_id("account_patricia"),
        90,
        250.00,
        100.00,
        models.PaymentStatus.PARTIAL,
        days_late=5,
        is_partial=True,
        installment_no=3,
        key_suffix="3",
    )
    add_past_payment(
        make_id("account_patricia"),
        60,
        280.00,
        120.00,
        models.PaymentStatus.PARTIAL,
        days_late=8,
        is_partial=True,
        installment_no=4,
        key_suffix="4",
    )
    add_past_payment(
        make_id("account_patricia"),
        30,
        310.00,
        100.00,
        models.PaymentStatus.PARTIAL,
        days_late=12,
        is_partial=True,
        installment_no=5,
        key_suffix="5",
    )
    add_upcoming_payment(make_id("account_patricia"), 4, 340.00, installment_no=6)

    # 5. Michael Missed: 4 on-time + 2 consecutive MISSED + 1 upcoming due in 3 days
    for i, offset in enumerate([180, 150, 120, 90], start=1):
        add_past_payment(
            make_id("account_michael"),
            offset,
            432.50,
            432.50,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    # 2 consecutive missed payments (due 60 and 30 days ago)
    add_past_payment(
        make_id("account_michael"),
        60,
        432.50,
        None,
        models.PaymentStatus.MISSED,
        days_late=60,
        retry_count=2,
        installment_no=5,
        key_suffix="5",
    )
    add_past_payment(
        make_id("account_michael"),
        30,
        432.50,
        None,
        models.PaymentStatus.MISSED,
        days_late=30,
        retry_count=1,
        installment_no=6,
        key_suffix="6",
    )
    add_upcoming_payment(make_id("account_michael"), 3, 432.50, installment_no=7)

    # 6. Helen Hardship: 3 on-time + 1 missed + 1 upcoming due in 6 days
    for i, offset in enumerate([120, 90, 60], start=1):
        add_past_payment(
            make_id("account_helen"),
            offset,
            275.40,
            275.40,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    add_past_payment(
        make_id("account_helen"),
        30,
        275.40,
        None,
        models.PaymentStatus.MISSED,
        days_late=30,
        installment_no=4,
        key_suffix="4",
    )
    add_upcoming_payment(make_id("account_helen"), 6, 275.40, installment_no=5)

    # 7. Daniel Default: 2 on-time + 3 MISSED (>90 days late) + 1 upcoming due in 2 days
    for i, offset in enumerate([150, 120], start=1):
        add_past_payment(
            make_id("account_daniel"),
            offset,
            334.60,
            334.60,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    # 3 consecutive missed payments with max days_late >= 90
    add_past_payment(
        make_id("account_daniel"),
        95,
        334.60,
        None,
        models.PaymentStatus.MISSED,
        days_late=95,
        retry_count=3,
        installment_no=3,
        key_suffix="3",
    )
    add_past_payment(
        make_id("account_daniel"),
        65,
        334.60,
        None,
        models.PaymentStatus.MISSED,
        days_late=65,
        retry_count=3,
        installment_no=4,
        key_suffix="4",
    )
    add_past_payment(
        make_id("account_daniel"),
        35,
        334.60,
        None,
        models.PaymentStatus.MISSED,
        days_late=35,
        retry_count=3,
        installment_no=5,
        key_suffix="5",
    )
    add_upcoming_payment(
        make_id("account_daniel"),
        2,
        334.60,
        installment_no=6,
        status=models.PaymentStatus.MISSED,
    )

    # 8. Lucas Live: 3 on-time + 1 late resolved + 1 upcoming due in 3 days
    for i, offset in enumerate([120, 90, 60], start=1):
        add_past_payment(
            make_id("account_lucas"),
            offset,
            428.90,
            428.90,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    add_past_payment(
        make_id("account_lucas"),
        30,
        428.90,
        428.90,
        models.PaymentStatus.LATE,
        days_late=14,
        installment_no=4,
        key_suffix="4",
    )
    add_upcoming_payment(make_id("account_lucas"), 3, 428.90, installment_no=5)

    # 9. Morgan Multi: Multi-Product
    # 9a. Personal Loan: 5 on-time + 1 upcoming due in 9 days
    for i, offset in enumerate([150, 120, 90, 60, 30], start=1):
        add_past_payment(
            make_id("account_morgan_loan"),
            offset,
            466.50,
            466.50,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=f"loan_{i}",
        )
    add_upcoming_payment(
        make_id("account_morgan_loan"), 9, 466.50, installment_no=6, key_suffix="loan_upcoming"
    )

    # 9b. Credit Card: 5 on-time + 1 upcoming due in 14 days
    for i, offset in enumerate([150, 120, 90, 60, 30], start=1):
        add_past_payment(
            make_id("account_morgan_card"),
            offset,
            210.00,
            210.00,
            models.PaymentStatus.ON_TIME,
            key_suffix=f"card_{i}",
        )
    add_upcoming_payment(
        make_id("account_morgan_card"), 14, 230.00, key_suffix="card_upcoming"
    )

    # 9c. Auto Loan: 3 on-time + 1 upcoming due in 4 days
    for i, offset in enumerate([90, 60, 30], start=1):
        add_past_payment(
            make_id("account_morgan_auto"),
            offset,
            462.80,
            462.80,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=f"auto_{i}",
        )
    add_upcoming_payment(
        make_id("account_morgan_auto"), 4, 462.80, installment_no=4, key_suffix="auto_upcoming"
    )

    # 10. Chloe Clean: 2 on-time + 1 upcoming due in 8 days
    for i, offset in enumerate([60, 30], start=1):
        add_past_payment(
            make_id("account_chloe"),
            offset,
            296.15,
            296.15,
            models.PaymentStatus.ON_TIME,
            installment_no=i,
            key_suffix=str(i),
        )
    add_upcoming_payment(make_id("account_chloe"), 8, 296.15, installment_no=3)

    # ---------------------------------------------------------------------------
    # 4. Account Activities (~26 snapshots, >=30d apart to support trend calculation)
    # ---------------------------------------------------------------------------
    activities = [
        # Sarah Steady: stable balances, 0 flags
        models.AccountActivity(
            id=make_id("act_sarah_1"),
            customer_id=make_id("customer_sarah_steady"),
            snapshot_date=today - timedelta(days=60),
            checking_balance=5200.00,
            savings_balance=14000.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=18,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_sarah_2"),
            customer_id=make_id("customer_sarah_steady"),
            snapshot_date=today - timedelta(days=30),
            checking_balance=5400.00,
            savings_balance=14500.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=15,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_sarah_3"),
            customer_id=make_id("customer_sarah_steady"),
            snapshot_date=today - timedelta(days=2),
            checking_balance=5350.00,
            savings_balance=15000.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=20,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        # Marcus Model: high reserves, 0 flags
        models.AccountActivity(
            id=make_id("act_marcus_1"),
            customer_id=make_id("customer_marcus_model"),
            snapshot_date=today - timedelta(days=60),
            checking_balance=8500.00,
            savings_balance=42000.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=12,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_marcus_2"),
            customer_id=make_id("customer_marcus_model"),
            snapshot_date=today - timedelta(days=30),
            checking_balance=9100.00,
            savings_balance=43500.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=10,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_marcus_3"),
            customer_id=make_id("customer_marcus_model"),
            snapshot_date=today - timedelta(days=3),
            checking_balance=9300.00,
            savings_balance=45000.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=14,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        # David Depleting: checking balance dropped from $4,500 to $1,900 (-57.78% > -20%)
        models.AccountActivity(
            id=make_id("act_david_1"),
            customer_id=make_id("customer_david_depleting"),
            snapshot_date=today - timedelta(days=60),
            checking_balance=4800.00,
            savings_balance=3500.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=8,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_david_2"),
            customer_id=make_id("customer_david_depleting"),
            snapshot_date=today - timedelta(days=35),
            checking_balance=4500.00,
            savings_balance=2800.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=12,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_david_3"),
            customer_id=make_id("customer_david_depleting"),
            snapshot_date=today - timedelta(days=2),
            checking_balance=1900.00,
            savings_balance=400.00,
            overdraft_count_30d=1,
            large_withdrawal_flag=True,
            salary_deposit_detected=True,
            app_logins_30d=25,
            support_contacts_30d=1,
            hardship_flag=False,
        ),
        # Patricia Partial: lower balances, frequent app logins
        models.AccountActivity(
            id=make_id("act_patricia_1"),
            customer_id=make_id("customer_patricia_partial"),
            snapshot_date=today - timedelta(days=40),
            checking_balance=1400.00,
            savings_balance=800.00,
            overdraft_count_30d=1,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=14,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_patricia_2"),
            customer_id=make_id("customer_patricia_partial"),
            snapshot_date=today - timedelta(days=4),
            checking_balance=950.00,
            savings_balance=300.00,
            overdraft_count_30d=2,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=19,
            support_contacts_30d=1,
            hardship_flag=False,
        ),
        # Michael Missed: salary deposit lost, multiple overdrafts
        models.AccountActivity(
            id=make_id("act_michael_1"),
            customer_id=make_id("customer_michael_missed"),
            snapshot_date=today - timedelta(days=65),
            checking_balance=3100.00,
            savings_balance=2200.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=8,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_michael_2"),
            customer_id=make_id("customer_michael_missed"),
            snapshot_date=today - timedelta(days=35),
            checking_balance=1200.00,
            savings_balance=500.00,
            overdraft_count_30d=2,
            large_withdrawal_flag=True,
            salary_deposit_detected=False,
            app_logins_30d=15,
            support_contacts_30d=1,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_michael_3"),
            customer_id=make_id("customer_michael_missed"),
            snapshot_date=today - timedelta(days=5),
            checking_balance=650.00,
            savings_balance=100.00,
            overdraft_count_30d=3,
            large_withdrawal_flag=False,
            salary_deposit_detected=False,
            app_logins_30d=22,
            support_contacts_30d=2,
            hardship_flag=False,
        ),
        # Helen Hardship: hardship_flag=True
        models.AccountActivity(
            id=make_id("act_helen_1"),
            customer_id=make_id("customer_helen_hardship"),
            snapshot_date=today - timedelta(days=45),
            checking_balance=2100.00,
            savings_balance=1500.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=6,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_helen_2"),
            customer_id=make_id("customer_helen_hardship"),
            snapshot_date=today - timedelta(days=3),
            checking_balance=420.00,
            savings_balance=0.00,
            overdraft_count_30d=1,
            large_withdrawal_flag=False,
            salary_deposit_detected=False,
            app_logins_30d=11,
            support_contacts_30d=3,
            hardship_flag=True,
        ),
        # Daniel Default: depleted funds, high overdrafts
        models.AccountActivity(
            id=make_id("act_daniel_1"),
            customer_id=make_id("customer_daniel_default"),
            snapshot_date=today - timedelta(days=70),
            checking_balance=600.00,
            savings_balance=0.00,
            overdraft_count_30d=4,
            large_withdrawal_flag=False,
            salary_deposit_detected=False,
            app_logins_30d=4,
            support_contacts_30d=2,
            hardship_flag=True,
        ),
        models.AccountActivity(
            id=make_id("act_daniel_2"),
            customer_id=make_id("customer_daniel_default"),
            snapshot_date=today - timedelta(days=5),
            checking_balance=45.00,
            savings_balance=0.00,
            overdraft_count_30d=6,
            large_withdrawal_flag=False,
            salary_deposit_detected=False,
            app_logins_30d=1,
            support_contacts_30d=4,
            hardship_flag=True,
        ),
        # Lucas Live: 50% checking balance drop, ready for live demo
        models.AccountActivity(
            id=make_id("act_lucas_1"),
            customer_id=make_id("customer_lucas_live"),
            snapshot_date=today - timedelta(days=40),
            checking_balance=3600.00,
            savings_balance=2800.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=10,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_lucas_2"),
            customer_id=make_id("customer_lucas_live"),
            snapshot_date=today - timedelta(days=4),
            checking_balance=1800.00,
            savings_balance=1200.00,
            overdraft_count_30d=1,
            large_withdrawal_flag=True,
            salary_deposit_detected=False,
            app_logins_30d=18,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        # Morgan Multi: healthy reserves across accounts
        models.AccountActivity(
            id=make_id("act_morgan_1"),
            customer_id=make_id("customer_morgan_multi"),
            snapshot_date=today - timedelta(days=60),
            checking_balance=7200.00,
            savings_balance=18000.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=14,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_morgan_2"),
            customer_id=make_id("customer_morgan_multi"),
            snapshot_date=today - timedelta(days=30),
            checking_balance=7500.00,
            savings_balance=19000.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=16,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_morgan_3"),
            customer_id=make_id("customer_morgan_multi"),
            snapshot_date=today - timedelta(days=3),
            checking_balance=7800.00,
            savings_balance=20000.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=15,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        # Chloe Clean: stable initial activity
        models.AccountActivity(
            id=make_id("act_chloe_1"),
            customer_id=make_id("customer_chloe_clean"),
            snapshot_date=today - timedelta(days=45),
            checking_balance=3400.00,
            savings_balance=4100.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=8,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
        models.AccountActivity(
            id=make_id("act_chloe_2"),
            customer_id=make_id("customer_chloe_clean"),
            snapshot_date=today - timedelta(days=5),
            checking_balance=3600.00,
            savings_balance=4300.00,
            overdraft_count_30d=0,
            large_withdrawal_flag=False,
            salary_deposit_detected=True,
            app_logins_30d=9,
            support_contacts_30d=0,
            hardship_flag=False,
        ),
    ]

    # ---------------------------------------------------------------------------
    # 5. Risk Features (Pre-calculated snapshots matching risk_job.py output)
    # ---------------------------------------------------------------------------
    risk_features = [
        # Sarah Steady: Healthy
        models.RiskFeature(
            id=make_id("risk_sarah"),
            customer_id=make_id("customer_sarah_steady"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=0,
            avg_days_late_90d=0.0,
            debt_to_income_ratio=0.18,
            credit_utilization_pct=15.0,
            balance_trend_30d=-0.93,
            early_warning_flag=False,
            defaulted=False,
        ),
        # Marcus Model: Healthy
        models.RiskFeature(
            id=make_id("risk_marcus"),
            customer_id=make_id("customer_marcus_model"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=0,
            avg_days_late_90d=0.0,
            debt_to_income_ratio=0.24,
            credit_utilization_pct=8.0,
            balance_trend_30d=2.20,
            early_warning_flag=False,
            defaulted=False,
        ),
        # David Depleting: early_warning_flag=True (balance drop -57.78% <= -20.0%)
        models.RiskFeature(
            id=make_id("risk_david"),
            customer_id=make_id("customer_david_depleting"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=0,
            avg_days_late_90d=0.0,
            debt_to_income_ratio=0.32,
            credit_utilization_pct=42.0,
            balance_trend_30d=-57.78,
            early_warning_flag=True,
            defaulted=False,
        ),
        # Patricia Partial: early_warning_flag=True (consecutive_partial_payments=3 >= 3)
        models.RiskFeature(
            id=make_id("risk_patricia"),
            customer_id=make_id("customer_patricia_partial"),
            as_of_date=today,
            consecutive_partial_payments=3,
            missed_payment_streak=0,
            avg_days_late_90d=8.33,
            debt_to_income_ratio=0.38,
            credit_utilization_pct=78.5,
            balance_trend_30d=-32.14,
            early_warning_flag=True,
            defaulted=False,
        ),
        # Michael Missed: early_warning_flag=True (missed_payment_streak=2 >= 2)
        models.RiskFeature(
            id=make_id("risk_michael"),
            customer_id=make_id("customer_michael_missed"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=2,
            avg_days_late_90d=45.0,
            debt_to_income_ratio=0.45,
            credit_utilization_pct=65.0,
            balance_trend_30d=-45.83,
            early_warning_flag=True,
            defaulted=False,
        ),
        # Helen Hardship: early_warning_flag=True (hardship_flag=True)
        models.RiskFeature(
            id=make_id("risk_helen"),
            customer_id=make_id("customer_helen_hardship"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=1,
            avg_days_late_90d=30.0,
            debt_to_income_ratio=0.55,
            credit_utilization_pct=88.0,
            balance_trend_30d=-80.00,
            early_warning_flag=True,
            defaulted=False,
        ),
        # Daniel Default: early_warning_flag=True & defaulted=True (missed_streak=3, max_days_late=95 >= 90)
        models.RiskFeature(
            id=make_id("risk_daniel"),
            customer_id=make_id("customer_daniel_default"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=3,
            avg_days_late_90d=65.0,
            debt_to_income_ratio=0.72,
            credit_utilization_pct=95.0,
            balance_trend_30d=-92.50,
            early_warning_flag=True,
            defaulted=True,
            days_to_default=0,
        ),
        # Lucas Live: early_warning_flag=True (balance drop -50.0%)
        models.RiskFeature(
            id=make_id("risk_lucas"),
            customer_id=make_id("customer_lucas_live"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=0,
            avg_days_late_90d=14.0,
            debt_to_income_ratio=0.29,
            credit_utilization_pct=38.0,
            balance_trend_30d=-50.00,
            early_warning_flag=True,
            defaulted=False,
        ),
        # Morgan Multi: Healthy portfolio borrower
        models.RiskFeature(
            id=make_id("risk_morgan"),
            customer_id=make_id("customer_morgan_multi"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=0,
            avg_days_late_90d=0.0,
            debt_to_income_ratio=0.31,
            credit_utilization_pct=26.5,
            balance_trend_30d=4.00,
            early_warning_flag=False,
            defaulted=False,
        ),
        # Chloe Clean: Healthy clean slate
        models.RiskFeature(
            id=make_id("risk_chloe"),
            customer_id=make_id("customer_chloe_clean"),
            as_of_date=today,
            consecutive_partial_payments=0,
            missed_payment_streak=0,
            avg_days_late_90d=0.0,
            debt_to_income_ratio=0.22,
            credit_utilization_pct=12.0,
            balance_trend_30d=5.88,
            early_warning_flag=False,
            defaulted=False,
        ),
    ]

    # ---------------------------------------------------------------------------
    # 6. Conversations & Messages (Seed 3-4 historical threads, rest clean)
    # ---------------------------------------------------------------------------
    conversations = [
        # Thread 1: Sarah Steady (Standard helpful reminder)
        models.Conversation(
            id=make_id("convo_sarah"),
            customer_id=make_id("customer_sarah_steady"),
            started_at=now - timedelta(days=25),
            last_message_at=now - timedelta(days=25, hours=2),
            channel=models.Channel.APP,
            is_escalated=False,
        ),
        # Thread 2: David Depleting (Proactive liquidity check-in)
        models.Conversation(
            id=make_id("convo_david"),
            customer_id=make_id("customer_david_depleting"),
            started_at=now - timedelta(days=10),
            last_message_at=now - timedelta(days=10, hours=1),
            channel=models.Channel.APP,
            is_escalated=False,
        ),
        # Thread 3: Michael Missed (Follow-up on missed payment)
        models.Conversation(
            id=make_id("convo_michael"),
            customer_id=make_id("customer_michael_missed"),
            started_at=now - timedelta(days=20),
            last_message_at=now - timedelta(days=20, hours=3),
            channel=models.Channel.APP,
            is_escalated=False,
        ),
        # Thread 4: Helen Hardship (Escalated human handoff on record)
        models.Conversation(
            id=make_id("convo_helen"),
            customer_id=make_id("customer_helen_hardship"),
            started_at=now - timedelta(days=15),
            last_message_at=now - timedelta(days=15, hours=1),
            channel=models.Channel.APP,
            is_escalated=True,
        ),
    ]

    messages = [
        # Messages for Sarah Steady
        models.Message(
            id=make_id("msg_sarah_1"),
            conversation_id=make_id("convo_sarah"),
            role=models.MessageRole.ASSISTANT,
            content="Hola Sarah, un recordatorio rápido de que el pago de tu préstamo personal de $367.82 está programado para débito automático el día 15.",
            created_at=now - timedelta(days=25, minutes=10),
            was_flagged=False,
        ),
        models.Message(
            id=make_id("msg_sarah_2"),
            conversation_id=make_id("convo_sarah"),
            role=models.MessageRole.USER,
            content="¡Gracias! La cuenta para el débito automático ya tiene fondos y está lista.",
            created_at=now - timedelta(days=25, minutes=5),
            was_flagged=False,
        ),
        # Messages for David Depleting
        models.Message(
            id=make_id("msg_david_1"),
            conversation_id=make_id("convo_david"),
            role=models.MessageRole.ASSISTANT,
            content="Hola David, espero que estés teniendo una buena semana. Tienes una cuota de tu préstamo personal de $365.12 que vence pronto. ¿Te gustaría revisar las opciones de pago o mantener tu calendario actual?",
            created_at=now - timedelta(days=10, minutes=20),
            was_flagged=False,
        ),
        models.Message(
            id=make_id("msg_david_2"),
            conversation_id=make_id("convo_david"),
            role=models.MessageRole.USER,
            content="¿Puedo ajustar la fecha de vencimiento unos días? Mi sueldo se deposita este viernes.",
            created_at=now - timedelta(days=10, minutes=15),
            was_flagged=False,
        ),
        models.Message(
            id=make_id("msg_david_3"),
            conversation_id=make_id("convo_david"),
            role=models.MessageRole.ASSISTANT,
            content="¡Por supuesto! Podemos evaluar la posibilidad de ajustar la fecha de tu ciclo de facturación para que coincida con tus fechas de pago. ¿Deseas que te comunique con un especialista para formalizar el cambio de fecha?",
            created_at=now - timedelta(days=10, minutes=10),
            was_flagged=False,
        ),
        # Messages for Michael Missed
        models.Message(
            id=make_id("msg_michael_1"),
            conversation_id=make_id("convo_michael"),
            role=models.MessageRole.ASSISTANT,
            content="Hola Michael, notamos que el pago de tu préstamo automotriz está vencido. Estamos aquí para ayudarte a ponerte al día. ¿De qué manera podemos apoyarte mejor con esta cuota?",
            created_at=now - timedelta(days=20, minutes=30),
            was_flagged=False,
        ),
        models.Message(
            id=make_id("msg_michael_2"),
            conversation_id=make_id("convo_michael"),
            role=models.MessageRole.USER,
            content="Tuve gastos médicos familiares imprevistos este mes. Estoy esperando mi próximo sueldo.",
            created_at=now - timedelta(days=20, minutes=20),
            was_flagged=False,
        ),
        models.Message(
            id=make_id("msg_michael_3"),
            conversation_id=make_id("convo_michael"),
            role=models.MessageRole.ASSISTANT,
            content="Gracias por contarnos, Michael, y espero que tu familia se encuentre mejor. Entendemos que surgen emergencias imprevistas. ¿Te gustaría explorar un plan de pagos temporal o dividir la cuota?",
            created_at=now - timedelta(days=20, minutes=15),
            was_flagged=False,
        ),
        # Messages for Helen Hardship
        models.Message(
            id=make_id("msg_helen_1"),
            conversation_id=make_id("convo_helen"),
            role=models.MessageRole.USER,
            content="Me despidieron de mi trabajo la semana pasada y no sé cómo voy a hacer mi próximo pago.",
            created_at=now - timedelta(days=15, minutes=10),
            was_flagged=False,
        ),
        models.Message(
            id=make_id("msg_helen_2"),
            conversation_id=make_id("convo_helen"),
            role=models.MessageRole.ASSISTANT,
            content="Te entiendo, y quiero asegurarme de que recibas ayuda adecuada con esto — te estoy comunicando con alguien de nuestro equipo en este momento.",
            created_at=now - timedelta(days=15, minutes=8),
            was_flagged=False,
        ),
    ]


    return {
        "customers": customers,
        "accounts": accounts,
        "payments": payments,
        "activities": activities,
        "risk_features": risk_features,
        "conversations": conversations,
        "messages": messages,
    }

