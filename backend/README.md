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

### 2. Start the Development Server
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

- `GET /`: Welcome message
- `GET /health`: Database connectivity check
- `GET /users`: Paginated list of users
- `POST /users`: Create a new user
- `GET /users/{user_id}`: Retrieve a user by ID

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

