# Boreal Entropy - Backend

FastAPI backend service configured with **SQLAlchemy 2.0** ORM and **PostgreSQL** (via `psycopg3`).

## Project Structure

```text
backend/
├── database.py       # Engine, SessionLocal, Base DeclarativeBase, and get_db dependency
├── models.py         # SQLAlchemy 2.0 declarative models (e.g., User)
├── schemas.py        # Pydantic validation & response schemas
├── main.py           # FastAPI application, lifespan table init, and route endpoints
├── pyproject.toml    # Project dependencies managed via uv
└── README.md         # Documentation
```

## Environment Variables

Database credentials can be configured either via a full connection string or individual variables (defaulting to the `.devcontainer` settings):

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | Optional full PostgreSQL connection string | Constructed from individual vars |
| `DB_USER` | Database username | `boreal` |
| `DB_PASSWORD` | Database password | `porfavor1,` |
| `DB_HOST` | Database host | `db` (or `localhost`) |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `entropy` |

## Getting Started

### 1. Install Dependencies
Dependencies are managed with `uv`:
```bash
cd backend
uv sync
```

### 2. Run Database Migrations & Seed Demo Personas
Database schema and mock demo personas are managed with **Alembic**:
```bash
uv run alembic upgrade head
```

To re-seed or reset demo mock data at any time:
```bash
uv run python seed.py --reset
```

To recompute nightly risk features across all customers:
```bash
uv run python risk_job.py
```

### 3. Start the Development Server
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

Interactive documentation with try-it-out capabilities is available at `/docs`.

### System
- `GET /`: Welcome message and version info
- `GET /health`: Database connectivity check

### Customers (`/customers`)
- `POST /customers`: Create a new customer
- `GET /customers`: List customers (supports pagination `skip`, `limit` and filters: `email`, `region`, `employment_status`)
- `GET /customers/{customer_id}`: Retrieve customer details
- `PUT` / `PATCH /customers/{customer_id}`: Update customer profile
- `DELETE /customers/{customer_id}`: Delete customer (cascades to accounts, activities, risk features)

### Accounts (`/accounts`)
- `POST /accounts`: Create a loan or credit account for a customer
- `GET /accounts`: List accounts (filters: `customer_id`, `product_type`, `is_active`)
- `GET /customers/{customer_id}/accounts`: List accounts for a specific customer
- `GET /accounts/{account_id}`: Retrieve account details
- `PUT` / `PATCH /accounts/{account_id}`: Update account information
- `DELETE /accounts/{account_id}`: Delete account (cascades to payments)

### Payments (`/payments`)
- `POST /payments`: Record a scheduled or completed payment
- `GET /payments`: List payments (filters: `account_id`, `status`)
- `GET /accounts/{account_id}/payments`: List payment schedule & history for an account
- `GET /payments/{payment_id}`: Retrieve payment details
- `PUT` / `PATCH /payments/{payment_id}`: Update payment record
- `DELETE /payments/{payment_id}`: Delete payment record

### Account Activity (`/account-activity`)
- `POST /account-activity`: Record account activity snapshot (balances, app logins, hardship)
- `GET /account-activity`: List activity snapshots (filters: `customer_id`, `hardship_flag`, `large_withdrawal_flag`)
- `GET /customers/{customer_id}/account-activity`: List activity snapshots for a customer
- `GET /account-activity/{activity_id}`: Retrieve activity snapshot details
- `PUT` / `PATCH /account-activity/{activity_id}`: Update activity snapshot
- `DELETE /account-activity/{activity_id}`: Delete activity snapshot

### Risk Features (`/risk-features`)
- `POST /risk-features`: Record calculated risk features
- `GET /risk-features`: List risk features (filters: `customer_id`, `early_warning_flag`, `defaulted`)
- `GET /customers/{customer_id}/risk-features`: List risk features for a customer
- `GET /risk-features/{feature_id}`: Retrieve risk feature details
- `PUT` / `PATCH /risk-features/{feature_id}`: Update risk feature record
- `DELETE /risk-features/{feature_id}`: Delete risk feature record
- `GET /customers/{customer_id}/early-warning`: Real-time early-warning risk indicator for prevention

### Chat & WhatsApp Simulation (`/ws/chat`, `/chat`)
- `WEBSOCKET /ws/chat/{room_id}`: Real-time multi-room WebSocket endpoint (`?sender_name=<name>`)
- `GET /chat/rooms`: List currently active chat rooms and user counts
- `GET /chat/rooms/{room_id}/messages`: Get recent message history for a room
- `POST /chat/rooms/{room_id}/messages`: Inject message into a room via REST (e.g. debt alert bots, notifications) and broadcast to active WebSockets
- `GET /chat/{room_id}`: Interactive WhatsApp-styled web chat interface for real-time simulation in your browser

## Working with Models

Models use modern SQLAlchemy 2.0 declarative syntax:
```python
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class MyModel(Base):
    __tablename__ = "my_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

New models imported into `models.py` or `main.py` are automatically created on startup via `init_db()`.

