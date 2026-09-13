"""
Unit tests for CustomerToneProfile and analyze_customer_tone in tone_analyzer.py.
"""

from unittest.mock import MagicMock

from tone_analyzer import analyze_customer_tone, CustomerToneProfile


def test_neutral_default_when_no_signals():
    profile = analyze_customer_tone(current_message="Hola, ¿qué tal?")
    assert isinstance(profile, CustomerToneProfile)
    assert profile.customer_tone == "neutral_matter_of_fact"
    assert profile.ai_tone == "professional_warm"
    assert profile.playback_rate == 1.00
    assert "Profesional" in profile.ai_tone_label_es
    assert "DIRECTIVA DE ADAPTACIÓN DE TONO" in profile.prompt_directive_es


def test_anxious_hardship_from_hardship_flag():
    activity = MagicMock(hardship_flag=True, large_withdrawal_flag=False)
    profile = analyze_customer_tone(activity=activity, current_message="Hola")
    assert profile.customer_tone == "anxious_hardship"
    assert profile.ai_tone == "empathetic_soothing"
    assert profile.playback_rate == 0.92
    assert "0.92x" in profile.pacing_label_es
    assert "hardship_flag_on_file" in profile.signals
    assert "VULNERABILIDAD" in profile.prompt_directive_es


def test_anxious_hardship_from_keywords():
    profile = analyze_customer_tone(
        current_message="Estoy muy preocupada, no me alcanza el dinero para llegar a fin de mes y perdí mi trabajo"
    )
    assert profile.customer_tone == "anxious_hardship"
    assert profile.ai_tone == "empathetic_soothing"
    assert profile.playback_rate == 0.92
    assert any("anxious_lexicon_matches" in s for s in profile.signals)


def test_frustrated_defensive_from_keywords():
    profile = analyze_customer_tone(
        current_message="Ya les dije mil veces que no me llamen, dejen de molestar o los voy a demandar"
    )
    assert profile.customer_tone == "frustrated_defensive"
    assert profile.ai_tone == "de_escalating_calm"
    assert profile.playback_rate == 0.95
    assert any("frustrated_lexicon_matches" in s for s in profile.signals)
    assert "DESESCALAR" in profile.prompt_directive_es.upper()


def test_confused_uncertain_from_keywords():
    profile = analyze_customer_tone(
        current_message="No me queda claro este monto, ¿de dónde sale y cuánto debo exactamente? Me pueden explicar"
    )
    assert profile.customer_tone == "confused_uncertain"
    assert profile.ai_tone == "clear_supportive"
    assert profile.playback_rate == 0.96
    assert any("confused_lexicon_matches" in s for s in profile.signals)


def test_cooperative_receptive_from_keywords():
    profile = analyze_customer_tone(
        current_message="Sí claro, quiero pagar hoy mismo por transferencia, ¿dónde puedo ver el enlace de pago? Muchas gracias"
    )
    assert profile.customer_tone == "cooperative_receptive"
    assert profile.ai_tone == "collaborative_efficient"
    assert profile.playback_rate == 1.03
    assert any("cooperative_lexicon_matches" in s for s in profile.signals)


def test_prosody_influences_tone():
    # Elevated vocal arousal with low valence (distress) tilts neutral message to anxious
    profile = analyze_customer_tone(
        current_message="Buenas tardes",
        prosody_arousal=0.78,
        prosody_valence=0.25,
        prosody_emotion_label="distressed",
    )
    assert profile.customer_tone == "anxious_hardship"
    assert profile.ai_tone == "empathetic_soothing"
    assert "prosody_label_distressed" in profile.signals


def test_helen_hardship_persona_prior():
    customer = MagicMock(full_name="Helen Hardship", credit_score=580, employment_status="unemployed")
    profile = analyze_customer_tone(customer=customer)
    assert profile.customer_tone == "anxious_hardship"
    assert "helen_hardship_profile" in profile.signals
    assert profile.playback_rate == 0.92


def test_marcus_model_persona_prior():
    customer = MagicMock(full_name="Marcus Model", credit_score=780, employment_status="employed")
    profile = analyze_customer_tone(customer=customer)
    assert profile.customer_tone == "cooperative_receptive"
    assert "marcus_model_profile" in profile.signals
    assert profile.playback_rate == 1.03


def test_to_dict_serialization():
    profile = analyze_customer_tone(current_message="Quiero pagar mi cuota")
    d = profile.to_dict()
    assert d["customer_tone"] == "cooperative_receptive"
    assert d["ai_tone"] == "collaborative_efficient"
    assert d["playback_rate"] == 1.03
    assert "rationale_es" in d
    assert "prompt_directive_es" in d

