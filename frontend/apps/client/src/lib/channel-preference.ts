export type ChannelPreference = 'chat' | 'call';

export interface CustomerPreferenceInfo {
  channel: ChannelPreference;
  label: string; // "Prefers Chat" | "Prefers Call"
  tag: string; // "Chat" | "Call"
  reason: string; // Behavioral explanation
}

// Known test personas mapping from seed/demo_data:
const KNOWN_PERSONA_PREFERENCES: Record<
  string,
  {
    channel: ChannelPreference;
    reasonEs: string;
    reasonEn: string;
  }
> = {
  'sarah.steady@example.com': {
    channel: 'chat',
    reasonEs: 'Uso activo de app móvil y mensajería',
    reasonEn: 'Active mobile app and messaging usage',
  },
  'marcus.model@example.com': {
    channel: 'call',
    reasonEs: 'Prefiere confirmación y asesoría telefónica directa',
    reasonEn: 'Prefers direct phone consultation and updates',
  },
  'david.depleting@example.com': {
    channel: 'chat',
    reasonEs: 'Comunicación digital asíncrona por app',
    reasonEn: 'Asynchronous digital communication in app',
  },
  'patricia.partial@example.com': {
    channel: 'call',
    reasonEs: 'Negociación verbal de acuerdos de pago',
    reasonEn: 'Verbal payment arrangement negotiation',
  },
  'michael.missed@example.com': {
    channel: 'call',
    reasonEs: 'Preferencia por línea telefónica tradicional',
    reasonEn: 'Traditional phone line preference',
  },
  'helen.hardship@example.com': {
    channel: 'call',
    reasonEs: 'Caso de vulnerabilidad — atención verbal empática',
    reasonEn: 'Hardship case — empathetic voice outreach',
  },
  'daniel.default@example.com': {
    channel: 'call',
    reasonEs: 'Mayor receptividad a contacto telefónico directo',
    reasonEn: 'Higher response rate to direct phone contact',
  },
  'lucas.live@example.com': {
    channel: 'chat',
    reasonEs: 'Activo en canal de chat web en vivo',
    reasonEn: 'Active on live web chat portal',
  },
  'morgan.multi@example.com': {
    channel: 'chat',
    reasonEs: 'Revisión escrita y detallada de cuentas múltiples',
    reasonEn: 'Written review for multi-product accounts',
  },
  'chloe.clean@example.com': {
    channel: 'chat',
    reasonEs: 'Perfil nativo digital y notificaciones app',
    reasonEn: 'Digital native profile & app notifications',
  },
};

export function getChannelPreference(
  customer: {
    id?: string;
    full_name?: string;
    email?: string;
    age?: number | null;
    credit_score?: number | null;
    employment_status?: string | null;
  } | null | undefined,
  lang: string = 'es'
): CustomerPreferenceInfo {
  const isSpanish = lang.startsWith('es');
  if (!customer) {
    return {
      channel: 'chat',
      label: isSpanish ? 'Prefiere Chat' : 'Prefers Chat',
      tag: 'Chat',
      reason: isSpanish ? 'Canal predeterminado' : 'Default channel',
    };
  }

  // 1. Direct match on known demo personas
  const emailLower = (customer.email || '').toLowerCase().trim();
  const nameLower = (customer.full_name || '').toLowerCase().trim();

  for (const [knownEmail, pref] of Object.entries(KNOWN_PERSONA_PREFERENCES)) {
    const knownPrefix = knownEmail.split('@')[0].replace('.', ' ');
    if (emailLower === knownEmail || nameLower.includes(knownPrefix)) {
      return {
        channel: pref.channel,
        label:
          pref.channel === 'call'
            ? isSpanish
              ? 'Prefiere Llamada'
              : 'Prefers Call'
            : isSpanish
            ? 'Prefiere Chat'
            : 'Prefers Chat',
        tag: pref.channel === 'call' ? (isSpanish ? 'Llamada' : 'Call') : 'Chat',
        reason: isSpanish ? pref.reasonEs : pref.reasonEn,
      };
    }
  }

  // 2. Behavioral simulation heuristics for any other customer
  const age = customer.age ?? 35;
  const creditScore = customer.credit_score ?? 700;
  const isUnemployed = customer.employment_status === 'unemployed';

  if (age >= 45) {
    return {
      channel: 'call',
      label: isSpanish ? 'Prefiere Llamada' : 'Prefers Call',
      tag: isSpanish ? 'Llamada' : 'Call',
      reason: isSpanish ? 'Preferencia telefónica generacional' : 'Phone communication preference',
    };
  }

  if (isUnemployed || creditScore < 610) {
    return {
      channel: 'call',
      label: isSpanish ? 'Prefiere Llamada' : 'Prefers Call',
      tag: isSpanish ? 'Llamada' : 'Call',
      reason: isSpanish ? 'Atención verbal personalizada' : 'Personalized verbal consultation',
    };
  }

  if (age < 35) {
    return {
      channel: 'chat',
      label: isSpanish ? 'Prefiere Chat' : 'Prefers Chat',
      tag: 'Chat',
      reason: isSpanish ? 'Interacción digital móvil' : 'Mobile digital messaging',
    };
  }

  // Deterministic fallback based on ID hash
  const hashVal = (customer.id || customer.full_name || '')
    .split('')
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const isCall = hashVal % 2 === 0;

  return {
    channel: isCall ? 'call' : 'chat',
    label: isCall
      ? isSpanish
        ? 'Prefiere Llamada'
        : 'Prefers Call'
      : isSpanish
      ? 'Prefiere Chat'
      : 'Prefers Chat',
    tag: isCall ? (isSpanish ? 'Llamada' : 'Call') : 'Chat',
    reason: isCall
      ? isSpanish
        ? 'Mayor receptividad a voz'
        : 'Higher voice engagement'
      : isSpanish
      ? 'Canal digital preferido'
      : 'Preferred digital channel',
  };
}

