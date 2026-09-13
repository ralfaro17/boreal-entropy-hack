"""
Comprehensive unit tests for the Bilingual Debt-Prevention Guardrails Engine.
"""

import pytest
from guardrails import (
    check_compliance_violations,
    customer_message_signals_distress,
    detect_customer_distress,
    get_escalation_reply,
    output_violates_guardrails,
    strip_accents,
    validate_compliance_or_raise,
)


class TestStripAccents:
    def test_strip_spanish_diacritics(self):
        assert strip_accents("Acción Legal y Buró") == "accion legal y buro"
        assert strip_accents("Nómina, embargo y pérdida") == "nomina, embargo y perdida"


class TestComplianceViolationsSpanish:
    @pytest.mark.parametrize(
        "threat_text, expected_category",
        [
            ("Te vamos a demandar en los tribunales si no pagas.", "legal_threat"),
            ("Iniciaremos acciones legales contra ti.", "legal_threat"),
            ("Vamos a proceder legalmente y abrir un litigio.", "legal_threat"),
            ("Nuestros abogados de cobranza tomarán tu caso.", "legal_threat"),
            ("Procederemos con el embargo de tus bienes.", "garnishment_threat"),
            ("Habrá retención de nómina para cubrir el adeudo.", "garnishment_threat"),
            ("Vamos a quitarle su auto por falta de pago.", "garnishment_threat"),
            ("Esto va a dañar tu buró de crédito permanentemente.", "credit_threat"),
            ("Vamos a reportarte al buró como moroso.", "credit_threat"),
            ("Vas a quedar boletinado en la lista negra.", "credit_threat"),
            ("Tu calificación crediticia va a manchar tu historial.", "credit_threat"),
            ("Turnaremos tu cuenta a un despacho de cobranza.", "collection_harassment"),
            ("Realizaremos visitas a domicilio si no atiendes.", "collection_harassment"),
            ("Vamos a notificar a tu jefe en tu trabajo sobre esta deuda.", "collection_harassment"),
            ("Eres un moroso irresponsable y mala paga.", "customer_shaming"),
            ("Te niegas a pagar y no quieres cumplir con tu palabra.", "customer_shaming"),
            ("Te garantizo un descuento del 50% en tu saldo total.", "unauthorized_promise"),
            ("Te prometo perdonar toda tu deuda hoy mismo.", "unauthorized_promise"),
            ("Por favor ingresa tu NIP para validar tu cuenta.", "credential_solicitation"),
            ("Danos tu contraseña y clave dinámica por seguridad.", "credential_solicitation"),
        ],
    )
    def test_spanish_violations_detected(self, threat_text: str, expected_category: str):
        violations = check_compliance_violations(threat_text)
        assert len(violations) >= 1, f"Expected violation in '{threat_text}'"
        categories = [v.category for v in violations]
        assert expected_category in categories
        assert output_violates_guardrails(threat_text) is not None

    def test_validate_compliance_or_raise(self):
        with pytest.raises(ValueError) as exc_info:
            validate_compliance_or_raise("Vamos a demandarte y embargar tu salario.")
        assert "violates fair debt collection guardrails" in str(exc_info.value)


class TestComplianceViolationsEnglish:
    @pytest.mark.parametrize(
        "threat_text, expected_category",
        [
            ("We are going to sue you in court.", "legal_threat"),
            ("Immediate legal action will be initiated.", "legal_threat"),
            ("We will garnish your wages next week.", "garnishment_threat"),
            ("We will seize your assets to recover the loan.", "garnishment_threat"),
            ("Your credit score will be damaged severely.", "credit_threat"),
            ("We are reporting you to the credit bureau as delinquent.", "credit_threat"),
            ("We are sending your case to a collections agency.", "collection_harassment"),
            ("We will contact your employer regarding this debt.", "collection_harassment"),
            ("You are an irresponsible deadbeat.", "customer_shaming"),
            ("I guarantee a discount on your principal balance.", "unauthorized_promise"),
            ("Please enter your PIN and security code.", "credential_solicitation"),
        ],
    )
    def test_english_violations_detected(self, threat_text: str, expected_category: str):
        violations = check_compliance_violations(threat_text)
        assert len(violations) >= 1
        categories = [v.category for v in violations]
        assert expected_category in categories


class TestCompliantMessagesPass:
    @pytest.mark.parametrize(
        "safe_message",
        [
            "Hola Carlos, te recordamos cordialmente que tu cuota de $120.00 vence mañana.",
            "Queremos apoyarte. ¿Deseas que revisemos un esquema de pago flexible?",
            "Estamos a tu disposición para coordinar una alternativa cómoda de pago.",
            "Hello Maria, friendly reminder that your payment is due on Oct 15.",
            "We understand unexpected events happen. Would you like to speak with a specialist?",
            "You can make your payment via the mobile app or online banking portal.",
        ],
    )
    def test_safe_messages_pass(self, safe_message: str):
        assert check_compliance_violations(safe_message) == []
        assert output_violates_guardrails(safe_message) is None
        # Should not raise
        validate_compliance_or_raise(safe_message)


class TestCustomerDistressDetection:
    @pytest.mark.parametrize(
        "distress_text, expected_category",
        [
            ("Lamentablemente perdí mi trabajo este mes.", "job_loss"),
            ("Me despidieron de la chamba y no tengo ingresos.", "job_loss"),
            ("Quedé desempleado hace dos semanas.", "job_loss"),
            ("No puedo pagar, no me alcanza el dinero para vivir.", "insolvency"),
            ("Estoy en quiebra y no tengo un peso para la cuota.", "insolvency"),
            ("Quedé en ceros este mes y no llego a la quincena.", "insolvency"),
            ("Tuve una emergencia médica y gastos médicos muy fuertes.", "medical_emergency"),
            ("Estoy hospitalizado tras una cirugía de urgencia.", "medical_emergency"),
            ("Falleció mi padre y tuvimos que cubrir los gastos del funeral.", "bereavement"),
            ("Estoy de luto por la muerte de mi esposo.", "bereavement"),
            ("Me van a desalojar de mi casa y no sé qué hacer.", "housing_crisis"),
            ("I lost my job and got laid off last week.", "job_loss"),
            ("I can't afford this payment right now, I have no money.", "insolvency"),
            ("My daughter had a medical emergency and is in the hospital.", "medical_emergency"),
            ("My mother passed away last week.", "bereavement"),
            ("I received an eviction notice today.", "housing_crisis"),
        ],
    )
    def test_distress_detected(self, distress_text: str, expected_category: str):
        is_distressed, categories = detect_customer_distress(distress_text)
        assert is_distressed is True, f"Failed to detect distress in: '{distress_text}'"
        assert expected_category in categories
        assert customer_message_signals_distress(distress_text) is True

    @pytest.mark.parametrize(
        "neutral_text",
        [
            "Hola, ¿cuál es el saldo de mi cuenta?",
            "Ya realicé mi abono por transferencia bancaria.",
            "¿Puedo pagar el viernes después de las 2 pm?",
            "Hello, could you confirm if you received my payment?",
            "I want to check my statement balance.",
        ],
    )
    def test_neutral_messages_do_not_trigger_distress(self, neutral_text: str):
        is_distressed, categories = detect_customer_distress(neutral_text)
        assert is_distressed is False
        assert categories == []
        assert customer_message_signals_distress(neutral_text) is False


class TestEscalationReplies:
    def test_spanish_escalation_reply(self):
        reply = get_escalation_reply("es")
        assert "especialista de nuestro equipo de apoyo financiero" in reply
        assert check_compliance_violations(reply) == []

    def test_english_escalation_reply(self):
        reply = get_escalation_reply("en")
        assert "financial support team" in reply
        assert check_compliance_violations(reply) == []

