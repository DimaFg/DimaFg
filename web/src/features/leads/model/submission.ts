import type { Values } from "./form";

export type SubmissionAttempt = { fingerprint: string; key: string };

export function normalizeValues(values: Values): Values {
  return {
    ...values,
    name: values.name.trim(),
    contact: values.contact.trim(),
    message: values.message.trim(),
    website: values.website.trim(),
  };
}

function newIdempotencyKey(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function resolveAttempt(
  previous: SubmissionAttempt | null,
  values: Values,
): SubmissionAttempt {
  // Сравниваем данные заявки, исключая время заполнения и атрибуцию.
  // Неизменённая заявка повторяется с тем же ключом; изменение создаёт новую попытку.
  const fingerprint = JSON.stringify(normalizeValues(values));
  return previous?.fingerprint === fingerprint
    ? previous
    : { fingerprint, key: newIdempotencyKey() };
}
