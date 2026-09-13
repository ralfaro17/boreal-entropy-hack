"""
Customer Tone Analyzer & Adaptive Voice Engine for Bancobranza.

This module evaluates customer tone across three signal layers:
1. Behavioral History: Hardship flags, missed payment streaks, partial payments, savings balance.
2. Conversation History & Lexical Markers: Sentiment, anxiety, frustration, confusion, or cooperation.
3. Real-time Vocal Prosody: Arousal, valence, pitch variability, and speech energy from ProsodyEmotionAnalyzer.

It computes an adaptive tone profile that drives:
- Contextual LLM prompt directives (empathy, pacing, vocabulary, opening validation).
- Acoustic speech delivery cadence (playback rate / pacing in Web Audio).
- Real-time visibility in the agent call console.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CustomerToneProfile:
    customer_tone: str  # "anxious_hardship" | "frustrated_defensive" | "confused_uncertain" | "cooperative_receptive" | "neutral_matter_of_fact"
    customer_tone_label_es: str
    customer_tone_label_en: str
    ai_tone: str  # "empathetic_soothing" | "de_escalating_calm" | "clear_supportive" | "collaborative_efficient" | "professional_warm"
    ai_tone_label_es: str
    ai_tone_label_en: str
    playback_rate: float  # e.g. 0.92 to 1.04
    pacing_label_es: str
    pacing_label_en: str
    rationale_es: str
    rationale_en: str
    signals: list[str] = field(default_factory=list)
    prompt_directive_es: str = ""
    prompt_directive_en: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_tone": self.customer_tone,
            "customer_tone_label_es": self.customer_tone_label_es,
            "customer_tone_label_en": self.customer_tone_label_en,
            "ai_tone": self.ai_tone,
            "ai_tone_label_es": self.ai_tone_label_es,
            "ai_tone_label_en": self.ai_tone_label_en,
            "playback_rate": round(self.playback_rate, 2),
            "pacing_label_es": self.pacing_label_es,
            "pacing_label_en": self.pacing_label_en,
            "rationale_es": self.rationale_es,
            "rationale_en": self.rationale_en,
            "signals": self.signals,
            "prompt_directive_es": self.prompt_directive_es,
            "prompt_directive_en": self.prompt_directive_en,
        }


# ---------------------------------------------------------------------------
# Lexical Marker Patterns (Regex)
# ---------------------------------------------------------------------------

ANXIOUS_PATTERNS = [
    r"\b(no tengo dinero|no me alcanza|no llego|no puedo pagar|imposible pagar)\b",
    r"\b(preocupad[oa]|angustiad[oa]|desesperad[oa]|ansiedad|estresad[oa]|estrés)\b",
    r"\b(perdí mi trabajo|sin trabajo|desemplead[oa]|quedé sin empleo)\b",
    r"\b(enfermedad|hospital|médic[oa]|gastos médicos|accidente|falleci|luto)\b",
    r"\b(ayuda por favor|no sé qué hacer|difícil situación|situación difícil|crisis)\b",
    r"\b(can'?t afford|no money|cannot pay|impossible to pay)\b",
    r"\b(worried|anxious|stress|stressed|desperate|panic)\b",
    r"\b(lost my job|unemployed|laid off|jobless)\b",
    r"\b(medical bill|hospital|sick|illness|accident|family emergency)\b",
    r"\b(help me|don'?t know what to do|in crisis|struggling)\b",
]

FRUSTRATED_PATTERNS = [
    r"\b(por qu[eé] llaman|por qu[eé] me llaman|dejen de llamar|dejen de molestar)\b",
    r"\b(ya les dije|ya pagu[eé]|ya report[eé]|hasta cu[aá]ndo|hart[oa])\b",
    r"\b(molest[oa]|furios[oa]|fastidi[oa]|injusto|acoso|amenaz)\b",
    r"\b(no voy a pagar|no me vuelvan a llamar|abogad[oa]|demanda)\b",
    r"\b(stop calling|why are you calling|quit calling|harassing|harassment)\b",
    r"\b(already told you|already paid|fed up|sick of this)\b",
    r"\b(angry|annoyed|furious|unfair|threat|scam)\b",
    r"\b(won'?t pay|never call again|lawyer)\b",
]

CONFUSED_PATTERNS = [
    r"\b(no entiendo|no comprendo|no me queda claro|qu[eé] es esto)\b",
    r"\b(cu[aá]nto debo|por qu[eé] debo|de d[oó]nde sale|desglose)\b",
    r"\b(me pueden explicar|no s[eé] de qu[eé] me habla|confundid[oa])\b",
    r"\b(don'?t understand|unclear|what is this|confused)\b",
    r"\b(how much do i owe|why do i owe|where is this from|breakdown)\b",
    r"\b(can you explain|what are you talking about)\b",
]

COOPERATIVE_PATTERNS = [
    r"\b(quiero pagar|c[oó]mo pago|d[oó]nde pago|c[oó]mo puedo pagar)\b",
    r"\b(de acuerdo|perfecto|s[ií] claro|con gusto|por supuesto)\b",
    r"\b(cu[aá]ndo puedo pagar|transferencia|tarjeta|link de pago|enlace de pago)\b",
    r"\b(muchas gracias|gracias|quiero ponerme al d[ií]a|acuerdo de pago)\b",
    r"\b(want to pay|how can i pay|where can i pay|ready to pay)\b",
    r"\b(agreed|perfect|yes sure|of course|gladly)\b",
    r"\b(payment link|transfer|debit card|credit card|pay now)\b",
    r"\b(thank you|thanks|want to settle|catch up|payment plan)\b",
]


def _match_count(text: str, patterns: list[str]) -> int:
    clean = text.lower()
    return sum(1 for p in patterns if re.search(p, clean, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Core Analysis Engine
# ---------------------------------------------------------------------------

def analyze_customer_tone(
    customer: Any | None = None,
    risk: Any | None = None,
    activity: Any | None = None,
    recent_messages: list[Any] | None = None,
    current_message: str = "",
    prosody_arousal: float | None = None,
    prosody_valence: float | None = None,
    prosody_pitch_hz: float | None = None,
    prosody_emotion_label: str | None = None,
) -> CustomerToneProfile:
    """Analyze customer signals and construct the adaptive AI tone profile."""

    scores = {
        "anxious_hardship": 0.0,
        "frustrated_defensive": 0.0,
        "confused_uncertain": 0.0,
        "cooperative_receptive": 0.0,
        "neutral_matter_of_fact": 1.0,  # default baseline
    }
    signals: list[str] = []

    # 1. Behavioral & Account Signals
    if activity and getattr(activity, "hardship_flag", False):
        scores["anxious_hardship"] += 3.5
        signals.append("hardship_flag_on_file")

    if activity and getattr(activity, "large_withdrawal_flag", False):
        scores["anxious_hardship"] += 1.0
        signals.append("large_withdrawal_detected")

    if risk:
        streak = getattr(risk, "missed_payment_streak", 0) or 0
        partials = getattr(risk, "consecutive_partial_payments", 0) or 0
        early_warn = getattr(risk, "early_warning_flag", False)

        if streak >= 2 or partials >= 2:
            scores["anxious_hardship"] += 1.5
            signals.append(f"payment_stress_streak_{streak}")
        elif streak == 1:
            scores["anxious_hardship"] += 0.8

        if early_warn:
            scores["anxious_hardship"] += 1.0
            signals.append("early_warning_active")

    if customer:
        credit_score = getattr(customer, "credit_score", None)
        emp_status = str(getattr(customer, "employment_status", "")).lower()
        cust_name = getattr(customer, "full_name", "").lower()

        if "unemployed" in emp_status:
            scores["anxious_hardship"] += 2.0
            signals.append("unemployed_status")

        if credit_score and credit_score >= 720 and not signals:
            scores["cooperative_receptive"] += 1.5
            signals.append("prime_credit_tier")

        # Specific demo persona priors
        if "helen" in cust_name:
            scores["anxious_hardship"] += 3.0
            signals.append("helen_hardship_profile")
        elif "marcus" in cust_name:
            scores["cooperative_receptive"] += 2.0
            signals.append("marcus_model_profile")
        elif "patricia" in cust_name:
            scores["cooperative_receptive"] += 1.0
            scores["anxious_hardship"] += 0.5
            signals.append("patricia_negotiation_profile")
        elif "daniel" in cust_name:
            scores["frustrated_defensive"] += 1.0
            signals.append("daniel_urgency_profile")

    # 2. Real-time Vocal Prosody Signals
    if prosody_arousal is not None:
        if prosody_arousal >= 0.65:
            if prosody_valence is not None and prosody_valence <= 0.40:
                scores["anxious_hardship"] += 2.5
                scores["frustrated_defensive"] += 2.0
                signals.append(f"vocal_high_arousal_low_valence ({prosody_arousal:.2f}/{prosody_valence:.2f})")
            else:
                scores["cooperative_receptive"] += 1.0
                scores["frustrated_defensive"] += 1.0
                signals.append(f"vocal_elevated_energy ({prosody_arousal:.2f})")
        elif prosody_arousal <= 0.35:
            scores["cooperative_receptive"] += 1.0
            scores["neutral_matter_of_fact"] += 1.0
            signals.append(f"vocal_calm_measured ({prosody_arousal:.2f})")

    if prosody_emotion_label == "distressed":
        scores["anxious_hardship"] += 3.0
        signals.append("prosody_label_distressed")
    elif prosody_emotion_label == "elevated":
        scores["frustrated_defensive"] += 1.5
        signals.append("prosody_label_elevated")
    elif prosody_emotion_label == "calm":
        scores["cooperative_receptive"] += 1.0
        scores["neutral_matter_of_fact"] += 1.0

    # 3. Textual Lexical Markers (Current Message & Recent History)
    all_user_texts = [current_message]
    if recent_messages:
        for msg in recent_messages[-4:]:
            content = getattr(msg, "content", "") if not isinstance(msg, dict) else msg.get("content", "")
            role = getattr(msg, "role", "") if not isinstance(msg, dict) else msg.get("role", "")
            if str(role).lower() in ("user", "customer", "models.messagerole.user"):
                cleaned = content.removeprefix("[voice] ").strip()
                if cleaned:
                    all_user_texts.append(cleaned)

    combined_text = " ".join(all_user_texts)

    anxious_hits = _match_count(combined_text, ANXIOUS_PATTERNS)
    frustrated_hits = _match_count(combined_text, FRUSTRATED_PATTERNS)
    confused_hits = _match_count(combined_text, CONFUSED_PATTERNS)
    cooperative_hits = _match_count(combined_text, COOPERATIVE_PATTERNS)

    if anxious_hits > 0:
        scores["anxious_hardship"] += anxious_hits * 3.0
        signals.append(f"anxious_lexicon_matches ({anxious_hits})")

    if frustrated_hits > 0:
        scores["frustrated_defensive"] += frustrated_hits * 3.5
        signals.append(f"frustrated_lexicon_matches ({frustrated_hits})")

    if confused_hits > 0:
        scores["confused_uncertain"] += confused_hits * 2.5
        signals.append(f"confused_lexicon_matches ({confused_hits})")

    if cooperative_hits > 0:
        scores["cooperative_receptive"] += cooperative_hits * 2.5
        signals.append(f"cooperative_lexicon_matches ({cooperative_hits})")

    # 4. Resolve Winning Category
    detected_tone = max(scores, key=scores.get)

    # 5. Build Adaptive Configuration
    if detected_tone == "anxious_hardship":
        ai_tone = "empathetic_soothing"
        playback_rate = 0.92
        tone_es = "Ansioso / Vulnerabilidad"
        tone_en = "Anxious / Hardship"
        ai_es = "Empático y Reconfortante"
        ai_en = "Empathetic & Soothing"
        pacing_es = "0.92x Pausado y Suave"
        pacing_en = "0.92x Gentle & Measured"
        rationale_es = "Se detectó vulnerabilidad económica o ansiedad emocional. La voz adopta un ritmo pausado con escucha empática."
        rationale_en = "Financial distress or anxiety detected. The voice adopts a gentle, measured cadence with deep empathy."
        directive_es = (
            "DIRECTIVA DE ADAPTACIÓN DE TONO (ESTADO: ANSIOSO / VULNERABILIDAD ECONÓMICA):\n"
            "- El cliente expresa preocupación, angustia o situación de dificultad económica.\n"
            "- Tono de voz: Sumamente empático, cálido, reconfortante y sin prisa.\n"
            "- Estilo: Inicia validando con compasión su situación ('Comprendo completamente...', 'No se preocupe, estamos aquí para apoyarle').\n"
            "- Cadencia: Frases cortas, respirables, sin tecnicismos ni exigencias de pago rígidas.\n"
            "- Propósito: Brindar tranquilidad y ofrecer opciones flexibles o enlace con especialista humano."
        )
        directive_en = (
            "TONE ADAPTATION DIRECTIVE (STATE: ANXIOUS / FINANCIAL HARDSHIP):\n"
            "- The customer is expressing financial worry, emotional strain, or a hardship circumstance.\n"
            "- Voice tone: Deeply empathetic, warm, soothing, and unhurried.\n"
            "- Style: Open with genuine validation ('I completely understand...', 'Please do not worry, we are here to support you').\n"
            "- Cadence: Short, breathing sentences; zero pressure or rigid payment demands.\n"
            "- Objective: Provide peace of mind, flexible restructuring, or connection to a human specialist."
        )

    elif detected_tone == "frustrated_defensive":
        ai_tone = "de_escalating_calm"
        playback_rate = 0.95
        tone_es = "Frustrado / Defensivo"
        tone_en = "Frustrated / Defensive"
        ai_es = "Desescalante y Sereno"
        ai_en = "De-escalating & Steady"
        pacing_es = "0.95x Firme y Sereno"
        pacing_en = "0.95x Steady & Grounded"
        rationale_es = "Se detectó irritación o resistencia. La voz modula a un tono firme, paciente y no defensivo para neutralizar tensión."
        rationale_en = "Friction or defensiveness detected. The voice modulates to a grounded, patient tempo to diffuse tension."
        directive_es = (
            "DIRECTIVA DE ADAPTACIÓN DE TONO (ESTADO: FRUSTRADO / DEFENSIVO):\n"
            "- El cliente manifiesta molestia, irritación o descontento con el contacto.\n"
            "- Tono de voz: Sereno, paciente, respetuoso y estrictamente no defensivo.\n"
            "- Estilo: Reconoce brevemente su molestia sin discutir ni recitar políticas ('Entiendo su molestia y le ofrezco una disculpa por el inconveniente...').\n"
            "- Cadencia: Pausado, claro y directo. No abrumes con explicaciones largas.\n"
            "- Propósito: Desescalar la fricción y plantear una vía de solución inmediata y sin fricciones."
        )
        directive_en = (
            "TONE ADAPTATION DIRECTIVE (STATE: FRUSTRATED / DEFENSIVE):\n"
            "- The customer is expressing annoyance, friction, or resistance to contact.\n"
            "- Voice tone: Steady, grounded, patient, respectful, and non-defensive.\n"
            "- Style: Acknowledge their annoyance cleanly without arguing ('I understand your frustration and apologize for the inconvenience...').\n"
            "- Cadence: Calm, clear, and direct. Avoid long corporate explanations.\n"
            "- Objective: De-escalate friction and present a straightforward, low-effort path forward."
        )

    elif detected_tone == "confused_uncertain":
        ai_tone = "clear_supportive"
        playback_rate = 0.96
        tone_es = "Confundido / Inseguro"
        tone_en = "Confused / Uncertain"
        ai_es = "Claro y Orientador"
        ai_en = "Clear & Educational"
        pacing_es = "0.96x Articulado y Claro"
        pacing_en = "0.96x Articulate & Structured"
        rationale_es = "El cliente necesita orientación sobre montos o conceptos. La voz articula de forma didáctica paso a paso."
        rationale_en = "The customer requires clarification regarding balances or terms. The voice speaks in a clear, structured step-by-step manner."
        directive_es = (
            "DIRECTIVA DE ADAPTACIÓN DE TONO (ESTADO: CONFUNDIDO / REQUIERE ORIENTACIÓN):\n"
            "- El cliente no tiene claridad sobre su cuota, fechas o conceptos de su cuenta.\n"
            "- Tono de voz: Didáctico, claro, paciente y accesible.\n"
            "- Estilo: Desglosa los datos con sencillez ('Con mucho gusto le explico los detalles de su cuenta...').\n"
            "- Cadencia: Articulada y bien estructurada, un punto a la vez.\n"
            "- Propósito: Aclarar dudas sin tecnicismos bancarios y verificar que todo haya quedado comprensible."
        )
        directive_en = (
            "TONE ADAPTATION DIRECTIVE (STATE: CONFUSED / NEEDS ORIENTATION):\n"
            "- The customer is unclear about their installment, due dates, or account breakdown.\n"
            "- Voice tone: Educational, patient, structured, and easy to follow.\n"
            "- Style: Explain figures simply without jargon ('I would be glad to break down your account details...').\n"
            "- Cadence: Articulate, one concept at a time.\n"
            "- Objective: Remove confusion and confirm clarity before moving forward."
        )

    elif detected_tone == "cooperative_receptive":
        ai_tone = "collaborative_efficient"
        playback_rate = 1.03
        tone_es = "Cooperativo / Receptivo"
        tone_en = "Cooperative / Receptive"
        ai_es = "Colaborativo y Ágil"
        ai_en = "Collaborative & Efficient"
        pacing_es = "1.03x Dinámico y Ágil"
        pacing_en = "1.03x Crisp & Dynamic"
        rationale_es = "El cliente muestra disposición para pagar. La voz responde de forma dinámica, positiva y orientada a la acción rápida."
        rationale_en = "The customer is cooperative and ready to resolve. The voice responds briskly, positively, and action-oriented."
        directive_es = (
            "DIRECTIVA DE ADAPTACIÓN DE TONO (ESTADO: COOPERATIVO / RECEPTIVO):\n"
            "- El cliente muestra excelente disposición y desea resolver su cuota o acuerdo.\n"
            "- Tono de voz: Positivo, dinámico, agradecido y resolutivo.\n"
            "- Estilo: Agradece la disposición y brinda los pasos concretos de inmediato ('Excelente, con gusto le facilito las opciones para que pueda liquidar...').\n"
            "- Cadencia: Fluida, ágil y ejecutiva.\n"
            "- Propósito: Concretar el acuerdo o pago de la forma más rápida y cómoda para el cliente."
        )
        directive_en = (
            "TONE ADAPTATION DIRECTIVE (STATE: COOPERATIVE / RECEPTIVE):\n"
            "- The customer is responsive and looking to settle their payment or installment.\n"
            "- Voice tone: Positive, upbeat, appreciative, and action-oriented.\n"
            "- Style: Acknowledge their cooperation warmly and provide actionable options immediately ('Wonderful, I can easily share the payment link or transfer details...').\n"
            "- Cadence: Fluid, crisp, and efficient.\n"
            "- Objective: Complete the payment arrangement smoothly with minimal friction."
        )

    else:
        ai_tone = "professional_warm"
        playback_rate = 1.00
        tone_es = "Neutro / Estándar"
        tone_en = "Neutral / Standard"
        ai_es = "Profesional y Cálido"
        ai_en = "Professional & Warm"
        pacing_es = "1.00x Cadencia Natural"
        pacing_en = "1.00x Natural Cadence"
        rationale_es = "Interacción estándar de consulta. La voz mantiene un tono cordial, equilibrado y profesional."
        rationale_en = "Standard informational interaction. The voice maintains a courteous, balanced, and professional cadence."
        directive_es = (
            "DIRECTIVA DE ADAPTACIÓN DE TONO (ESTADO: NEUTRO / PROFESIONAL):\n"
            "- El cliente realiza consultas estándar de forma tranquila.\n"
            "- Tono de voz: Cortés, cálido, profesional y equilibrado.\n"
            "- Cadencia: Natural y fluida a velocidad estándar.\n"
            "- Propósito: Atender la consulta y orientar amablemente sobre sus cuotas de Bancobranza."
        )
        directive_en = (
            "TONE ADAPTATION DIRECTIVE (STATE: NEUTRAL / PROFESSIONAL):\n"
            "- The customer is inquiring calmly in a standard dialogue.\n"
            "- Voice tone: Courteous, warm, professional, and balanced.\n"
            "- Cadence: Natural and fluid at standard pacing.\n"
            "- Objective: Address the inquiry attentively and guide them on their Bancobranza account."
        )

    return CustomerToneProfile(
        customer_tone=detected_tone,
        customer_tone_label_es=tone_es,
        customer_tone_label_en=tone_en,
        ai_tone=ai_tone,
        ai_tone_label_es=ai_es,
        ai_tone_label_en=ai_en,
        playback_rate=playback_rate,
        pacing_label_es=pacing_es,
        pacing_label_en=pacing_en,
        rationale_es=rationale_es,
        rationale_en=rationale_en,
        signals=signals,
        prompt_directive_es=directive_es,
        prompt_directive_en=directive_en,
    )

