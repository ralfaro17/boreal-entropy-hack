"""
AI-assisted payment reminder chat — full implementation.

Flow: customer message -> distress check -> load/create conversation ->
parallel context fetch -> prompt build -> streamed model response ->
guardrail check -> persist both messages -> customer.

Run: uvicorn chat_service:app --reload
Env: ANTHROPIC_API_KEY must be set.
"""

import asyncio
import re
from datetime import date, datetime

import models
from anthropic import AsyncAnthropic
from database import get_db, init_db
from guardrails import (
    customer_message_signals_distress,
    get_escalation_reply,
    output_violates_guardrails,
)
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

app = FastAPI(title="Payment Reminder Chat")
client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env

MODEL = "deepseek-v4-flash"  # fast model: latency over raw capability here
MAX_HISTORY_MESSAGES = 10  # trimmed context window, keeps prompts small and fast


@app.on_event("startup")
def on_startup():
    init_db()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None  # omit to start a new conversation
    language: str = "es"  # "es" (default) or "en"


# ---------------------------------------------------------------------------
# 1. Context aggregation (run all DB lookups concurrently)
# ---------------------------------------------------------------------------

def _sync_get_customer(db: Session, customer_id: str):
    return db.get(models.Customer, customer_id)


def _sync_get_next_payment(db: Session, customer_id: str):
    return (
        db.query(models.Payment)
        .join(models.Account)
        .filter(models.Account.customer_id == customer_id)
        .filter(models.Payment.payment_date.is_(None))
        .order_by(models.Payment.due_date.asc())
        .first()
    )


def _sync_get_latest_risk(db: Session, customer_id: str):
    return (
        db.query(models.RiskFeature)
        .filter_by(customer_id=customer_id)
        .order_by(models.RiskFeature.as_of_date.desc())
        .first()
    )


def _sync_get_latest_activity(db: Session, customer_id: str):
    return (
        db.query(models.AccountActivity)
        .filter_by(customer_id=customer_id)
        .order_by(models.AccountActivity.snapshot_date.desc())
        .first()
    )


async def gather_context(db: Session, customer_id: str) -> dict:
    """Fetch everything needed to personalize the reminder, in parallel.
    Sync SQLAlchemy calls are offloaded to threads so they don't block
    the event loop or each other."""
    customer, payment, risk, activity = await asyncio.gather(
        asyncio.to_thread(_sync_get_customer, db, customer_id),
        asyncio.to_thread(_sync_get_next_payment, db, customer_id),
        asyncio.to_thread(_sync_get_latest_risk, db, customer_id),
        asyncio.to_thread(_sync_get_latest_activity, db, customer_id),
    )
    if customer is None:
        raise HTTPException(404, "Customer not found")

    days_until_due = (payment.due_date - date.today()).days if payment else None

    return {
        "name": customer.full_name,
        "amount_due": float(payment.amount_due) if payment else None,
        "due_date": payment.due_date.isoformat() if payment else None,
        "days_until_due": days_until_due,
        "missed_streak": risk.missed_payment_streak if risk else 0,
        "early_warning": risk.early_warning_flag if risk else False,
        "hardship_flag": activity.hardship_flag if activity else False,
    }


# ---------------------------------------------------------------------------
# 2. Conversation persistence
# ---------------------------------------------------------------------------

def _sync_get_conversation(db: Session, conversation_id: str) -> models.Conversation | None:
    return db.get(models.Conversation, conversation_id)


def _sync_create_conversation(db: Session, customer_id: str) -> models.Conversation:
    convo = models.Conversation(customer_id=customer_id)
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def _sync_get_recent_messages(db: Session, conversation_id: str, limit: int) -> list[models.Message]:
    messages = (
        db.query(models.Message)
        .filter_by(conversation_id=conversation_id)
        .order_by(models.Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


def _sync_add_message(
    db: Session, conversation_id: str, role: models.MessageRole, content: str, flagged: bool = False
) -> None:
    db.add(
        models.Message(
            conversation_id=conversation_id, role=role, content=content, was_flagged=flagged
        )
    )
    convo = db.get(models.Conversation, conversation_id)
    if convo:
        convo.last_message_at = datetime.utcnow()
    db.commit()


def _sync_mark_escalated(db: Session, conversation_id: str) -> None:
    convo = db.get(models.Conversation, conversation_id)
    if convo:
        convo.is_escalated = True
        db.commit()


async def get_or_create_conversation(
    db: Session, customer_id: str, conversation_id: str | None
) -> models.Conversation:
    if conversation_id:
        convo = await asyncio.to_thread(_sync_get_conversation, db, conversation_id)
        if convo is None or convo.customer_id != customer_id:
            raise HTTPException(404, "Conversation not found for this customer")
        return convo
    return await asyncio.to_thread(_sync_create_conversation, db, customer_id)


async def load_history(db: Session, conversation_id: str) -> list[dict]:
    """Return prior turns as Anthropic message dicts, oldest first."""
    messages = await asyncio.to_thread(
        _sync_get_recent_messages, db, conversation_id, MAX_HISTORY_MESSAGES
    )
    role_map = {models.MessageRole.USER: "user", models.MessageRole.ASSISTANT: "assistant"}
    return [
        {"role": role_map[m.role], "content": m.content}
        for m in messages
        if m.role in role_map
    ]


# ---------------------------------------------------------------------------
# 3. Prompt construction — tone and compliance rules baked in
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE_ES = """Eres un asistente de recordatorio y asesoría de pagos para un banco. Tu labor \
es ayudar a {name} a mantenerse al día con su pago próximo o vencido mediante una conversación de chat \
breve, empática, cálida y sin juzgar — jamás a través de la presión ni la intimidación.

Contexto del cliente:
- Monto adeudado: {amount_due}
- Fecha de vencimiento: {due_date} ({days_until_due} días desde hoy)
- Racha de pagos no realizados: {missed_streak}
- Alerta temprana de riesgo: {early_warning}
- Indicador de dificultad económica: {hardship_flag}

Reglas estrictas e inviolables:
- Jamás amenaces con demandas, juicios, abogados o acciones legales.
- Jamás amenaces con dañar el buró de crédito, manchar historial o listas negras.
- Jamás amenaces con embargos, retención de sueldo o cobradores.
- Jamás avergüences al cliente ni le recrimines su situación personal.
- Jamás prometas descuentos o condonaciones específicas no autorizadas. Ofrece canalizarlo con un especialista.
- Finaliza siempre con un siguiente paso concreto y sencillo (pagar ahora, reprogramar o hablar con un asesor).
- Si hardship_flag es verdadero, no repitas la exigencia de pago; prioriza ofrecer alternativas flexibles y apoyo humano.
- Si el cliente expresa dificultades económicas o desempleo, prioriza ofrecer ayuda y transferencia a un asesor.
- Mensajes breves (menos de 80 palabras). Sin tecnicismos corporativos ni signos de exclamación excesivos.
- Utiliza el historial para dar continuidad natural a la conversación.
"""

SYSTEM_PROMPT_TEMPLATE_EN = """You are a payment reminder assistant for a bank. Your job \
is to help {name} stay on top of an upcoming or overdue payment through a short, \
warm, non-judgmental chat conversation — never through pressure.

Customer context:
- Amount due: {amount_due}
- Due date: {due_date} ({days_until_due} days from today)
- Missed-payment streak: {missed_streak}
- Early warning flag: {early_warning}
- Hardship flag on file: {hardship_flag}

Hard rules, never break these:
- Never threaten legal action, wage garnishment, asset seizure, or credit damage.
- Never shame the customer or imply they are irresponsible.
- Never promise a specific fee waiver, interest change, or discount — you are not \
authorized to make financial commitments. Offer to connect them with a specialist instead.
- Always end with one concrete, low-friction next step (pay now, reschedule, or talk to someone).
- If hardship_flag is true, do not repeat the payment ask — instead, gently open the \
door to flexible options and offer to connect them with a human advisor.
- If the customer expresses financial distress, job loss, or inability to pay, stop \
selling the payment and prioritize offering help and a human handoff.
- Keep each message under 80 words. No corporate jargon, no exclamation points stacked up.
- Use the conversation history for continuity — don't repeat information you already gave.
"""


def build_system_prompt(ctx: dict, language: str = "es") -> str:
    template = SYSTEM_PROMPT_TEMPLATE_ES if language == "es" else SYSTEM_PROMPT_TEMPLATE_EN
    return template.format(**ctx)


# ---------------------------------------------------------------------------
# 4. Endpoint — streamed response, escalation on distress, full persistence
# ---------------------------------------------------------------------------

@app.post("/chat/{customer_id}")
async def chat(customer_id: str, payload: ChatRequest, db: Session = Depends(get_db)):
    convo = await get_or_create_conversation(db, customer_id, payload.conversation_id)

    # Persist the incoming message before doing anything else, so it's
    # never lost even if the model call fails downstream.
    await asyncio.to_thread(
        _sync_add_message, db, convo.id, models.MessageRole.USER, payload.message
    )

    if customer_message_signals_distress(payload.message):
        await asyncio.to_thread(_sync_mark_escalated, db, convo.id)
        escalation_reply = get_escalation_reply(payload.language)
        await asyncio.to_thread(
            _sync_add_message, db, convo.id, models.MessageRole.ASSISTANT, escalation_reply
        )

        async def escalation_stream():
            yield escalation_reply

        return StreamingResponse(
            escalation_stream(),
            media_type="text/plain",
            headers={"X-Conversation-Id": convo.id, "X-Escalated": "true"},
        )

    ctx = await gather_context(db, customer_id)
    system_prompt = build_system_prompt(ctx, payload.language)
    history = await load_history(db, convo.id)  # includes the message just saved

    async def token_stream():
        buffer = []
        async with client.messages.stream(
            model=MODEL,
            max_tokens=200,
            system=system_prompt,
            messages=history,
        ) as stream:
            async for text in stream.text_stream:
                buffer.append(text)
                yield text

        full_text = "".join(buffer)
        violation = output_violates_guardrails(full_text)
        flagged = violation is not None
        if flagged:
            flag_note = (
                "\n\n[Este mensaje fue marcado para revisión regulatoria y será atendido por un especialista.]"
                if payload.language == "es"
                else "\n\n[This message was flagged for compliance review and will be followed up on by a team member.]"
            )
            yield flag_note

        await asyncio.to_thread(
            _sync_add_message,
            db,
            convo.id,
            models.MessageRole.ASSISTANT,
            full_text,
            flagged,
        )
        if flagged:
            await asyncio.to_thread(_sync_mark_escalated, db, convo.id)

    return StreamingResponse(
        token_stream(),
        media_type="text/plain",
        headers={"X-Conversation-Id": convo.id},
    )


@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db)):
    convo = db.get(models.Conversation, conversation_id)
    if not convo:
        raise HTTPException(404, "Conversation not found")
    return [
        {"role": m.role.value, "content": m.content, "created_at": m.created_at, "flagged": m.was_flagged}
        for m in convo.messages
    ]