import type { LeadCreated } from "../api/leads";

export type Values = {
  name: string;
  contact: string;
  service: string;
  message: string;
  consent: boolean;
  website: string;
};

export type FieldName = Exclude<keyof Values, "website">;
export type Errors = Partial<Record<FieldName, string>>;
export type Status =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string }
  | { kind: "success"; result: LeadCreated };

export const FIELD_ORDER: FieldName[] = ["name", "contact", "service", "message", "consent"];
export const LIMITS = { name: [2, 100], contact: [3, 200], message: [0, 3000] } as const;

export function validate(v: Values): Errors {
  const errors: Errors = {};
  const name = v.name.trim();
  if (name.length < LIMITS.name[0]) errors.name = "Как к вам обращаться? Минимум 2 символа.";
  else if (name.length > LIMITS.name[1]) errors.name = `Не больше ${LIMITS.name[1]} символов.`;
  else if (!/\p{L}/u.test(name)) errors.name = "Укажите имя буквами.";

  const contact = v.contact.trim();
  if (contact.length < LIMITS.contact[0]) errors.contact = "Укажите Telegram, e-mail или телефон.";
  else if (contact.length > LIMITS.contact[1]) errors.contact = `Не больше ${LIMITS.contact[1]} символов.`;

  if (v.message.length > LIMITS.message[1]) errors.message = `Не больше ${LIMITS.message[1]} символов.`;
  if (!v.consent) errors.consent = "Без согласия я не смогу обработать заявку.";
  return errors;
}

export type LeadServiceOption = { slug: string; formLabel: string };
