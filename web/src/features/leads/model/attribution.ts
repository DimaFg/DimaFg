/**
 * First-touch атрибуция: UTM-метки, внешний referrer и страница входа сохраняются при первом
 * визите и прикладываются к заявке. Хранится только в браузере посетителя, в аналитику не уходит.
 */
const KEY = "lead_attribution_v1";
const TTL_MS = 30 * 24 * 60 * 60 * 1000;
const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"] as const;

export type Attribution = {
  referrer?: string | null;
  landing_page?: string | null;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  utm_term?: string | null;
  utm_content?: string | null;
};

type Stored = { capturedAt: number; data: Attribution };

function clip(value: string | null | undefined, max: number): string | null {
  if (!value) return null;
  return value.slice(0, max);
}

function read(): Stored | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Stored;
    if (Date.now() - parsed.capturedAt > TTL_MS) return null;
    return parsed;
  } catch {
    return null;
  }
}

function externalReferrer(): string | null {
  if (!document.referrer) return null;
  try {
    const ref = new URL(document.referrer);
    if (ref.host === window.location.host) return null;
    // Только origin и путь: query string referrer'а может содержать чужие персональные данные.
    return `${ref.origin}${ref.pathname}`;
  } catch {
    return null;
  }
}

export function captureAttribution(): void {
  const params = new URLSearchParams(window.location.search);
  const hasUtm = UTM_KEYS.some((k) => params.get(k));
  // Новый визит с UTM-метками перезаписывает старую атрибуцию; без меток — сохраняем первую.
  if (read() && !hasUtm) return;

  const data: Attribution = {
    referrer: clip(externalReferrer(), 500),
    landing_page: clip(window.location.pathname, 500),
  };
  for (const k of UTM_KEYS) data[k] = clip(params.get(k), 200);
  try {
    window.localStorage.setItem(KEY, JSON.stringify({ capturedAt: Date.now(), data }));
  } catch {
    // приватный режим или запрет хранилища — атрибуция просто не сохранится
  }
}

export function getAttribution(): Attribution | null {
  if (typeof window === "undefined") return null;
  return read()?.data ?? null;
}
