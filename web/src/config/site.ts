/**
 * Открытые бизнес-решения (домен, контакты, версия политики и т. п.) задаются переменными
 * окружения NEXT_PUBLIC_*. Значения по умолчанию — тестовые, из прототипа.
 */
function env(value: string | undefined, fallback: string): string {
  return value && value.trim() ? value.trim() : fallback;
}

const telegramHandle = env(process.env.NEXT_PUBLIC_TELEGRAM_HANDLE, "experement0");
const channelHandle = env(process.env.NEXT_PUBLIC_TELEGRAM_CHANNEL, "your_channel");

export const site = {
  url: env(process.env.NEXT_PUBLIC_SITE_URL, "http://localhost:3000").replace(/\/$/, ""),
  /** production | staging | local. Вне production сайт закрыт от индексации. */
  environment: env(process.env.NEXT_PUBLIC_SITE_ENV, "local"),
  photographerName: env(process.env.NEXT_PUBLIC_PHOTOGRAPHER_NAME, "Дмитрий"),
  name: "Дмитрий — уличная фотография",
  shortName: "Д·МИТРИЙ",
  description:
    "Уличная и документальная фотография в Москве: съёмка мероприятий, личные фотосеты, фотопрогулки и съёмка для брендов.",
  locale: "ru_RU",
  region: env(process.env.NEXT_PUBLIC_SERVICE_AREA, "Москва и область"),
  responseTime: "обычно в течение суток",
  copyrightYear: env(process.env.NEXT_PUBLIC_COPYRIGHT_YEAR, "2026"),
  email: env(process.env.NEXT_PUBLIC_CONTACT_EMAIL, "mail@mail.ru"),
  telegram: {
    handle: telegramHandle,
    url: `https://t.me/${telegramHandle}`,
  },
  telegramChannel: {
    handle: channelHandle,
    url: `https://t.me/${channelHandle}`,
  },
  privacyPolicyVersion: env(process.env.NEXT_PUBLIC_PRIVACY_POLICY_VERSION, "2026-10-draft"),
  apiBaseUrl: env(process.env.NEXT_PUBLIC_API_BASE_URL, "").replace(/\/$/, ""),
} as const;

export const isProduction = site.environment === "production";
