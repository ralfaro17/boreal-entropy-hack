"""
Debt Prevention & Compliance Guardrails Engine (Bilingual: Spanish & English).

Provides regulatory and ethical guardrails for fair debt collection and customer protection:
1. Prohibited outputs (legal threats, wage/asset seizure, credit score threats, harassment, shaming, unauthorized promises).
2. Proactive distress and hardship detection (job loss, insolvency, healthcare emergencies, bereavement, housing crisis).
3. Context-aware empathetic escalation responses for specialist handoff.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Sequence


def strip_accents(text: str) -> str:
    """Normalize text by converting to lowercase and stripping combining diacritical marks."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


@dataclass(frozen=True)
class GuardrailRule:
    category: str
    pattern: str
    description: str
    severity: str = "critical"  # "critical" (regulatory violation) | "warning"


@dataclass(frozen=True)
class ComplianceViolation:
    category: str
    description: str
    matched_text: str
    severity: str


# ===========================================================================
# 1. BANNED REGULATORY & COMPLIANCE PATTERNS
# ===========================================================================

# Legal / Judicial Action Threats
BANNED_LEGAL_PATTERNS: list[GuardrailRule] = [
    GuardrailRule(
        category="legal_threat",
        pattern=r"\b(we (will|are going to)|going to) sue\b",
        description="Threat of lawsuit or suing customer",
    ),
    GuardrailRule(
        category="legal_threat",
        pattern=r"\blegal action(s)?\b",
        description="Threat of legal action",
    ),
    GuardrailRule(
        category="legal_threat",
        pattern=r"\b(lawsuit|court action|litigation|prosecute|prosecution)\b",
        description="Reference to court proceedings or litigation",
    ),
    GuardrailRule(
        category="legal_threat",
        pattern=r"\b(demandar(emos)?|te vamos a demandar|vamos a proceder legalmente)\b",
        description="Amenaza de demanda judicial",
    ),
    GuardrailRule(
        category="legal_threat",
        pattern=r"\baccion(es)? legal(es)?\b",
        description="Mención o amenaza de acciones legales",
    ),
    GuardrailRule(
        category="legal_threat",
        pattern=r"\b(proceso judicial|demanda judicial|juicio mercantil|litigio|tribunales?|ir a corte)\b",
        description="Amenaza de proceso judicial o tribunales",
    ),
    GuardrailRule(
        category="legal_threat",
        pattern=r"\babogados? de cobranza\b",
        description="Intimidación con abogados o bufetes de cobranza",
    ),
]

# Asset Seizure & Wage Garnishment Threats
BANNED_GARNISHMENT_PATTERNS: list[GuardrailRule] = [
    GuardrailRule(
        category="garnishment_threat",
        pattern=r"\bgarnish(ment)?\b",
        description="Wage or account garnishment threat",
    ),
    GuardrailRule(
        category="garnishment_threat",
        pattern=r"\b(seize|repossess(ion)?|confiscate) (your )?(assets?|property|salary|wages?|car|house)\b",
        description="Threat of asset seizure or repossession",
    ),
    GuardrailRule(
        category="garnishment_threat",
        pattern=r"\b(embargo|embargar|orden de embargo)\b",
        description="Amenaza de embargo de bienes o cuentas",
    ),
    GuardrailRule(
        category="garnishment_threat",
        pattern=r"\b(retencion|congelar|retirar) (de )?(sueldo|salario|nomina|cuentas?)\b",
        description="Amenaza de retención de salario o fondos",
    ),
    GuardrailRule(
        category="garnishment_threat",
        pattern=r"\b(quitar(le|te)?|despojar(le|te)?) (de )?(tus?|sus?) (bienes|casa|propiedad|auto|vehiculo)\b",
        description="Amenaza de privar de bienes o patrimonio",
    ),
]

# Credit Bureau Threats & Blacklisting
BANNED_CREDIT_THREAT_PATTERNS: list[GuardrailRule] = [
    GuardrailRule(
        category="credit_threat",
        pattern=r"\bcredit (score|report|rating) (will|may|could) (be )?(damaged?|hurt|suffered?|ruined?|dropped?)\b",
        description="Threat of damage to credit score or credit rating",
    ),
    GuardrailRule(
        category="credit_threat",
        pattern=r"\b(ruin|destroy|tank|damage|hurt|impact) (your )?credit (score|report|rating)?\b",
        description="Threat to destroy customer credit",
    ),
    GuardrailRule(
        category="credit_threat",
        pattern=r"\b(report(ing)? you to (the )?credit bureau|blacklist(ed)?)\b",
        description="Threat of credit bureau reporting or blacklisting",
    ),
    GuardrailRule(
        category="credit_threat",
        pattern=r"\b(danar|afectar|arruinar|manchar|destruir) (tu |su )?(historial|credito|score|buro)\b",
        description="Amenaza de dañar o manchar historial o buró de crédito",
    ),
    GuardrailRule(
        category="credit_threat",
        pattern=r"\b(reportar(te|le)? al buro|enviar(te|le)? a buro de credito)\b",
        description="Amenaza de reportar negativamente ante buró de crédito",
    ),
    GuardrailRule(
        category="credit_threat",
        pattern=r"\b(lista negra|boletinar(te|le)?|marcar(te|le)? como moros[oa])\b",
        description="Amenaza de boletinar o ingresar en listas negras",
    ),
]

# Collection Agency Harassment & Third-Party Contact
BANNED_COLLECTION_AGENCY_PATTERNS: list[GuardrailRule] = [
    GuardrailRule(
        category="collection_harassment",
        pattern=r"\bcollections? agency\b",
        description="Threat of turning debt over to third-party collections agency",
    ),
    GuardrailRule(
        category="collection_harassment",
        pattern=r"\b(contact|notify) your (employer|boss|family|neighbors|coworkers)\b",
        description="Threat of disclosing debt to employer or family",
    ),
    GuardrailRule(
        category="collection_harassment",
        pattern=r"\b(send (agents|reps) to your home|visit you at work)\b",
        description="Threat of invasive in-person visits",
    ),
    GuardrailRule(
        category="collection_harassment",
        pattern=r"\b(agencia|despacho) de cobranza(s)?\b",
        description="Amenaza de turnar a agencia o despacho de cobranza",
    ),
    GuardrailRule(
        category="collection_harassment",
        pattern=r"\b(visita(s)? a domicilio|visita extrajudicial|cobradores en tu puerta)\b",
        description="Amenaza de visitas intimidatorias en el domicilio",
    ),
    GuardrailRule(
        category="collection_harassment",
        pattern=r"\b(avisar|notificar|contactar) a tu (jefe|empleador|trabajo|familia|vecinos)\b",
        description="Amenaza de contactar a familiares, empleadores o terceros",
    ),
]

# Customer Shaming & Harassment
BANNED_SHAMING_PATTERNS: list[GuardrailRule] = [
    GuardrailRule(
        category="customer_shaming",
        pattern=r"\b(deadbeat|irresponsible|refusing to pay|shameful|untrustworthy)\b",
        description="Shaming, insulting, or disparaging customer character",
    ),
    GuardrailRule(
        category="customer_shaming",
        pattern=r"\b(moros[oa]|mala paga|irresponsable|sinverguenza|descarad[oa])\b",
        description="Calificativos despectivos o estigmatizantes hacia el cliente",
    ),
    GuardrailRule(
        category="customer_shaming",
        pattern=r"\b(te niegas a pagar|no quieres cumplir|falta de verguenza|no tienes palabra)\b",
        description="Juicios de valor o recriminaciones sobre la conducta del cliente",
    ),
]

# Unauthorized Financial Commitments & Guarantees
BANNED_UNAUTHORIZED_PROMISES_PATTERNS: list[GuardrailRule] = [
    GuardrailRule(
        category="unauthorized_promise",
        pattern=r"\bguarantee(d)? (a |the )?(discount|waiver|reduction|debt forgiveness)\b",
        description="Unauthorized guarantee of financial concession or forgiveness",
    ),
    GuardrailRule(
        category="unauthorized_promise",
        pattern=r"\b(waive all your (fees|interest)|forgive your (entire )?debt)\b",
        description="Unauthorized commitment to waive fees or forgive principal",
    ),
    GuardrailRule(
        category="unauthorized_promise",
        pattern=r"\b(te garantizo|garantizamos|te aseguro) (un |una )?(descuento|quita|condonacion|rebaja)\b",
        description="Garantía no autorizada de quita, condonación o descuento",
    ),
    GuardrailRule(
        category="unauthorized_promise",
        pattern=r"\b(perdonar(emos)? (toda )?tu deuda|eliminar(emos)? todos los intereses garantizado)\b",
        description="Compromiso no autorizado de condonación total",
    ),
]

# Prohibited Credential Requests (Security / Anti-Phishing)
BANNED_CREDENTIAL_PATTERNS: list[GuardrailRule] = [
    GuardrailRule(
        category="credential_solicitation",
        pattern=r"\b(give (me|us)|enter|provide) your (pin|password|security code|cvv|cvc)\b",
        description="Requesting sensitive credentials or payment card codes",
    ),
    GuardrailRule(
        category="credential_solicitation",
        pattern=r"\b(ingresa|danos|proporciona|escribe) tu (nip|contrasena|clave dinamica|codigo de seguridad|cvv|cvc)\b",
        description="Solicitud indebida de NIP, contraseñas o códigos de seguridad",
    ),
]

# Master list of all regulatory banned patterns
ALL_BANNED_RULES: list[GuardrailRule] = [
    *BANNED_LEGAL_PATTERNS,
    *BANNED_GARNISHMENT_PATTERNS,
    *BANNED_CREDIT_THREAT_PATTERNS,
    *BANNED_COLLECTION_AGENCY_PATTERNS,
    *BANNED_SHAMING_PATTERNS,
    *BANNED_UNAUTHORIZED_PROMISES_PATTERNS,
    *BANNED_CREDENTIAL_PATTERNS,
]


# ===========================================================================
# 2. CUSTOMER DISTRESS & HARDSHIP PATTERNS
# ===========================================================================

@dataclass(frozen=True)
class DistressCategory:
    category: str
    patterns: Sequence[str]
    description: str


DISTRESS_CATEGORIES: list[DistressCategory] = [
    DistressCategory(
        category="job_loss",
        description="Loss of employment or reduction in work income",
        patterns=[
            r"\blost my job\b",
            r"\b(got |was )?laid off\b",
            r"\bunemployed\b",
            r"\bfired from my job\b",
            r"\bperdi (mi )?(trabajo|empleo|chamba|laburo|pega)\b",
            r"\bme (despidieron|corrieron|liquidaron)\b",
            r"\bquede desemplead[oa]\b",
            r"\bsin (trabajo|empleo|chamba|ingresos?)\b",
            r"\bme quedo sin trabajo\b",
        ],
    ),
    DistressCategory(
        category="insolvency",
        description="Severe lack of funds or inability to afford living necessities",
        patterns=[
            r"\bcan'?t afford\b",
            r"\bno money\b",
            r"\bcannot pay\b",
            r"\bcan'?t pay\b",
            r"\bbankrupt(cy)?\b",
            r"\bbroke\b",
            r"\bfinancial (hardship|crisis|trouble|difficult(y|ies))\b",
            r"\bno puedo pagar\b",
            r"\bno me alcanza\b",
            r"\bno tengo (dinero|plata|fondos|un peso|un centavo|recursos)\b",
            r"\bestoy en (bancarrota|quiebra)\b",
            r"\bquede en ceros?\b",
            r"\bno llego a (fin de mes|la quincena)\b",
            r"\bno tengo ni para (comer|los medicamentos|la comida)\b",
            r"\bsobreendeudad[oa]\b",
            r"\bimposible pagar\b",
        ],
    ),
    DistressCategory(
        category="medical_emergency",
        description="Critical medical issues, hospitalization, or expensive treatments",
        patterns=[
            r"\bmedical emergency\b",
            r"\b(in the )?hospital(ized)?\b",
            r"\bserious illness\b",
            r"\bmedical (expenses|bills|costs)\b",
            r"\bemergencia medica\b",
            r"\bgastos medicos\b",
            r"\b(estoy )?hospitalizad[oa]\b",
            r"\benfermedad grave\b",
            r"\btratamiento medico costoso\b",
            r"\baccidente grave\b",
            r"\bcirugia de urgencia\b",
        ],
    ),
    DistressCategory(
        category="bereavement",
        description="Death in family or mourning costs",
        patterns=[
            r"\bdeath in (the |my )?family\b",
            r"\bpassed away\b",
            r"\bfuneral expenses\b",
            r"\bfallecio (mi |un )?(espos[oa]|madre|padre|hijo|hija|herman[oa]|familiar)\b",
            r"\bmurio (mi |un )?(espos[oa]|madre|padre|hijo|hija|herman[oa]|familiar)\b",
            r"\bestoy de luto\b",
            r"\bgastos (del |de )?funeral\b",
        ],
    ),
    DistressCategory(
        category="housing_crisis",
        description="Eviction, foreclosure, or disaster damage",
        patterns=[
            r"\bevict(ed|ion)?\b",
            r"\bforeclos(ed|ure)\b",
            r"\bhomeless\b",
            r"\bdesalojo\b",
            r"\bme van a desalojar\b",
            r"\bquede en la calle\b",
            r"\bperdi mi casa\b",
            r"\bdesastre natural\b",
        ],
    ),
]


# ===========================================================================
# 3. VERIFICATION & MATCHING FUNCTIONS
# ===========================================================================

def check_compliance_violations(text: str) -> list[ComplianceViolation]:
    """Inspect text against all regulatory guardrail rules.
    Matches are tested against normalized text without diacritics.
    """
    if not text or not text.strip():
        return []

    normalized = strip_accents(text)
    violations: list[ComplianceViolation] = []

    for rule in ALL_BANNED_RULES:
        match = re.search(rule.pattern, normalized, flags=re.IGNORECASE)
        if match:
            violations.append(
                ComplianceViolation(
                    category=rule.category,
                    description=rule.description,
                    matched_text=match.group(0),
                    severity=rule.severity,
                )
            )

    return violations


def output_violates_guardrails(text: str) -> str | None:
    """Convenience checker returning the pattern / description of the first violation found,
    or None if the text complies with all debt prevention standards and domain boundaries.
    """
    violations = check_compliance_violations(text)
    if violations:
        return f"[{violations[0].category}] {violations[0].description} ('{violations[0].matched_text}')"

    is_off, cat = detect_off_topic(text)
    if is_off:
        return f"[off_topic_violation] Content breaches domain boundary (category: {cat})"

    return None


def detect_customer_distress(text: str) -> tuple[bool, list[str]]:
    """Detect if a customer's message expresses life hardship or financial distress.
    Returns (has_distress, list_of_detected_categories).
    """
    if not text or not text.strip():
        return False, []

    normalized = strip_accents(text)
    detected: list[str] = []

    for cat in DISTRESS_CATEGORIES:
        for pat in cat.patterns:
            if re.search(pat, normalized, flags=re.IGNORECASE):
                if cat.category not in detected:
                    detected.append(cat.category)
                break

    return (len(detected) > 0, detected)


def customer_message_signals_distress(text: str) -> bool:
    """Boolean helper to quickly check if a customer message warrants immediate escalation."""
    has_distress, _ = detect_customer_distress(text)
    return has_distress


def validate_compliance_or_raise(text: str, context: str = "Message") -> None:
    """Raise a ValueError with details if the given text violates debt collection compliance rules."""
    violations = check_compliance_violations(text)
    if violations:
        details = "; ".join(f"{v.description} ('{v.matched_text}')" for v in violations)
        raise ValueError(
            f"{context} violates fair debt collection guardrails: {details}"
        )


# ===========================================================================
# 4. ESCALATION & HUMAN HANDOFF RESPONSES
# ===========================================================================

ESCALATION_REPLIES = {
    "es": (
        "Comprendemos totalmente tu situación y lamentamos las dificultades que estás atravesando. "
        "En este momento te estoy transfiriendo con un especialista de nuestro equipo de apoyo financiero "
        "para evaluar juntos alternativas y esquemas de pago flexibles adaptados a tu caso."
    ),
    "en": (
        "We completely understand your situation and are sorry for the difficulties you are facing. "
        "I am connecting you right now with a specialist from our financial support team "
        "to review flexible arrangement options and find a solution that works for you."
    ),
}


def get_escalation_reply(language: str = "es") -> str:
    """Return an empathetic, non-punitive specialist handoff message in the requested language."""
    return ESCALATION_REPLIES.get(language.lower(), ESCALATION_REPLIES["es"])


# ===========================================================================
# 5. OFF-TOPIC & DOMAIN BOUNDARY GUARDRAILS (Anti-Drift / Anti-Jailbreak)
# ===========================================================================

@dataclass(frozen=True)
class OffTopicRule:
    category: str
    pattern: str
    description: str


OFF_TOPIC_RULES: list[OffTopicRule] = [
    # Culinary / Cooking / Recipes
    OffTopicRule(
        category="culinary_recipe",
        pattern=r"\b(receta(s)?|ingredientes?|como (cocinar|hornear)|(receta de|como (preparar|cocinar|hornear|hacer)) (un |una )?(tarta|pastel|torta|galleta(s)?|postre|pan|sopa|bizcocho|comida)|tarta|pastel|torta|galletas|precalienta(r)? el horno|harina de trigo|polvo de hornear)\b",
        description="Consulta sobre recetas o cocina",
    ),
    OffTopicRule(
        category="culinary_recipe",
        pattern=r"\b(recipe(s)?|ingredients?|how to (cook|bake)|(recipe for|how to (bake|cook|make)) (a |an )?(cake|pie|cookie(s)?|dessert|bread|soup|pastry|meal)|cake|pie|cookies|chocolate cake|preheat the oven|cup(s)? of flour)\b",
        description="Cooking or food recipe inquiry",
    ),
    # Mathematics / LaTeX / Physics formulas
    OffTopicRule(
        category="math_latex",
        pattern=r"(\\begin\{|\\frac\{|\\sqrt\{|\\int|\\sum|\\cdot|\$\$|\\\[|\\mathrm|\\alpha|\\beta|\\theta|\\partial)",
        description="LaTeX mathematical typesetting markup",
    ),
    OffTopicRule(
        category="math_latex",
        pattern=r"\b(latex|ecuacion(es)? diferencial(es)?|teorema de pitagoras|integral definida|derivada(s)? parcial(es)?|formula cuadratica)\b",
        description="Consulta académica sobre matemáticas o fórmulas LaTeX",
    ),
    OffTopicRule(
        category="math_latex",
        pattern=r"\b(differential equation(s)?|pythagorean theorem|quadratic formula|eigenvalue(s)?|fourier transform)\b",
        description="Academic mathematics or physics request",
    ),
    # Coding / Scripting / Code Generation
    OffTopicRule(
        category="coding_scripting",
        pattern=r"\b(escribe|generar?|hazme|crear?|write|generate|give me)\s+(un\s+|una\s+|a\s+|an\s+)?((python|javascript|java|c\+\+|c#|bash|powershell|rust|sql|html)\s+(script|codigo|code|programa|program|funcion|function)|(script|codigo|code|programa|program|funcion|function)\s+(en\s+|in\s+|de\s+)?(python|javascript|java|c\+\+|c#|bash|powershell|rust|sql|html))\b",
        description="Solicitud de código de programación o scripts",
    ),
    OffTopicRule(
        category="coding_scripting",
        pattern=r"(```(python|javascript|bash|c|cpp|java|rust|go|php|ruby)|import requests|def main\(\)|console\.log\(|public static void main)",
        description="Fragmento o bloque de código de programación",
    ),
    # Jailbreak / Roleplay Manipulation / Persona Escape
    OffTopicRule(
        category="jailbreak_roleplay",
        pattern=r"\b(ignora (todas )?las instrucciones|ignore (all )?(previous )?instructions|dan mode|jailbreak|olvida tu rol|forget your role|act as an unrestricted|pretend you are|haz como si fueras|ahora eres un)\b",
        description="Intento de evasión de rol o jailbreak",
    ),
    # Creative writing / General trivia / Homework
    OffTopicRule(
        category="creative_trivia",
        pattern=r"\b(escribe un poema|write a poem|cuentame un chiste|tell me a joke|escribe una cancion|write a song|cuentame un cuento|tell me a story|quien (gano|descubrio|invento)|who (won|discovered|invented)|cual es la capital de|what is the capital of)\b",
        description="Solicitud de poesía, chistes o trivia general",
    ),
]


OFF_TOPIC_REFUSALS = {
    "es": (
        "Como asistente de Boreal Bank, únicamente puedo orientarte sobre temas relacionados con "
        "tus cuentas bancarias, cuotas, estados de cuenta y opciones de pago. "
        "¿Deseas que revisemos los detalles o alternativas para tu cuota pendiente?"
    ),
    "en": (
        "As a Boreal Bank assistant, I can only assist with inquiries regarding your bank accounts, "
        "installments, account statements, and payment arrangement options. "
        "Would you like to review options for your pending installment?"
    ),
}


def detect_off_topic(text: str) -> tuple[bool, str | None]:
    """Detect if a user's message is asking for off-topic non-banking content
    (e.g., cake recipes, LaTeX formulas, coding, jailbreak manipulation).
    Returns (is_off_topic, detected_category_or_None).
    """
    if not text or not text.strip():
        return False, None

    normalized = strip_accents(text)
    for rule in OFF_TOPIC_RULES:
        # Check both normalized text and raw text (so backslashes in LaTeX are preserved)
        if re.search(rule.pattern, normalized, flags=re.IGNORECASE) or re.search(rule.pattern, text, flags=re.IGNORECASE):
            return True, rule.category

    return False, None


def get_off_topic_refusal(language: str = "es") -> str:
    """Return a polite, firm refusal redirecting the customer to their bank account and installments."""
    return OFF_TOPIC_REFUSALS.get(language.lower(), OFF_TOPIC_REFUSALS["es"])


def output_is_off_topic(text: str) -> bool:
    """Post-generation check: verify that the assistant's output does not inadvertently leak
    LaTeX math blocks, cooking recipes, or code snippets.
    """
    is_off, _ = detect_off_topic(text)
    return is_off

