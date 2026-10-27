"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useId, useRef, useState } from "react";

import { site } from "@/config/site";
import { ApiError, type LeadCreated, NetworkError, submitLead } from "@/lib/api/leads";
import { getAttribution } from "@/lib/attribution";
import type { Service } from "@/lib/types";

type Values = {
  name: string;
  contact: string;
  service: string;
  message: string;
  consent: boolean;
  website: string;
};

type FieldName = Exclude<keyof Values, "website">;
type Errors = Partial<Record<FieldName, string>>;
type Status =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string }
  | { kind: "success"; result: LeadCreated };

const FIELD_ORDER: FieldName[] = ["name", "contact", "service", "message", "consent"];
const LIMITS = { name: [2, 100], contact: [3, 200], message: [0, 3000] } as const;

function newIdempotencyKey(): string {
  // randomUUID нет в Safari < 15.4 и вне HTTPS
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function validate(v: Values): Errors {
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

type Props = { services: Service[]; defaultService?: string };

export function LeadForm({ services, defaultService }: Props) {
  const initial: Values = {
    name: "",
    contact: "",
    service: defaultService ?? services[0]?.slug ?? "other",
    message: "",
    consent: false,
    website: "",
  };
  const [values, setValues] = useState<Values>(initial);
  const [errors, setErrors] = useState<Errors>({});
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  const formRef = useRef<HTMLFormElement>(null);
  const successRef = useRef<HTMLHeadingElement>(null);
  const shownAt = useRef<number | null>(null);
  const idempotencyKey = useRef<string | null>(null);
  const inFlight = useRef(false);
  const uid = useId();
  const id = (field: string) => `${uid}-${field}`;

  useEffect(() => {
    shownAt.current = Date.now();
  }, []);

  useEffect(() => {
    if (status.kind === "success") successRef.current?.focus();
  }, [status.kind]);

  function update<K extends keyof Values>(field: K, value: Values[K]) {
    setValues((v) => ({ ...v, [field]: value }));
    if (field in errors) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field as FieldName];
        return next;
      });
    }
  }

  function focusFirstError(errs: Errors) {
    const first = FIELD_ORDER.find((f) => errs[f]);
    if (first) formRef.current?.querySelector<HTMLElement>(`#${CSS.escape(id(first))}`)?.focus();
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (inFlight.current) return;

    const clientErrors = validate(values);
    setErrors(clientErrors);
    if (Object.keys(clientErrors).length > 0) {
      setStatus({ kind: "idle" });
      focusFirstError(clientErrors);
      return;
    }

    // Один ключ на одну заявку: повтор после сетевой ошибки не создаст дубль на сервере.
    idempotencyKey.current ??= newIdempotencyKey();
    inFlight.current = true;
    setStatus({ kind: "submitting" });
    try {
      const result = await submitLead(
        {
          name: values.name.trim(),
          contact: values.contact.trim(),
          service: values.service,
          message: values.message.trim(),
          consent: values.consent,
          privacy_policy_version: site.privacyPolicyVersion,
          website: values.website,
          elapsed_ms: shownAt.current ? Date.now() - shownAt.current : null,
          attribution: getAttribution(),
        },
        idempotencyKey.current,
      );
      setStatus({ kind: "success", result });
    } catch (err) {
      setStatus({ kind: "error", message: describeError(err, setErrors, focusFirstError) });
    } finally {
      inFlight.current = false;
    }
  }

  function reset() {
    setValues({ ...initial, service: values.service });
    setErrors({});
    idempotencyKey.current = null;
    shownAt.current = Date.now();
    setStatus({ kind: "idle" });
  }

  if (status.kind === "success") {
    return (
      <div className="form-success" role="status">
        <h3 ref={successRef} tabIndex={-1}>
          Заявка отправлена
        </h3>
        <p>
          Номер заявки: <span className="mono">№{status.result.public_number}</span>.
          <br />
          Отвечу {status.result.expected_response} — в Telegram или на почту, которые вы указали.
        </p>
        <button type="button" className="btn btn-ghost" onClick={reset}>
          Отправить ещё одну
        </button>
      </div>
    );
  }

  const submitting = status.kind === "submitting";
  const fieldProps = (field: FieldName) => ({
    id: id(field),
    name: field,
    "aria-invalid": errors[field] ? true : undefined,
    "aria-describedby": errors[field] ? id(`${field}-error`) : undefined,
  });
  const errorText = (field: FieldName) =>
    errors[field] ? (
      <p className="field-error" id={id(`${field}-error`)}>
        {errors[field]}
      </p>
    ) : null;

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate aria-busy={submitting} aria-label="Заявка на съёмку">
      <div className="field">
        <label htmlFor={id("name")}>Имя</label>
        <input
          {...fieldProps("name")}
          type="text"
          autoComplete="name"
          placeholder="Как к вам обращаться"
          maxLength={LIMITS.name[1]}
          required
          value={values.name}
          onChange={(e) => update("name", e.target.value)}
        />
        {errorText("name")}
      </div>

      <div className="field">
        <label htmlFor={id("contact")}>Telegram или e-mail</label>
        <input
          {...fieldProps("contact")}
          type="text"
          autoComplete="email"
          inputMode="email"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="@username или name@example.ru"
          maxLength={LIMITS.contact[1]}
          required
          value={values.contact}
          onChange={(e) => update("contact", e.target.value)}
        />
        {errorText("contact")}
      </div>

      <div className="field">
        <label htmlFor={id("service")}>Интересует</label>
        <select {...fieldProps("service")} value={values.service} onChange={(e) => update("service", e.target.value)}>
          {services.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.formLabel}
            </option>
          ))}
          <option value="other">Другое</option>
        </select>
        {errorText("service")}
      </div>

      <div className="field">
        <label htmlFor={id("message")}>Сообщение</label>
        <textarea
          {...fieldProps("message")}
          placeholder="Расскажите, что хотите снять"
          maxLength={LIMITS.message[1]}
          value={values.message}
          onChange={(e) => update("message", e.target.value)}
        />
        {errorText("message")}
      </div>

      <div className="hp-field" aria-hidden="true">
        <label htmlFor={id("website")}>Не заполняйте это поле</label>
        <input
          id={id("website")}
          name="website"
          type="text"
          tabIndex={-1}
          autoComplete="off"
          value={values.website}
          onChange={(e) => update("website", e.target.value)}
        />
      </div>

      <div className="field-check">
        <input
          {...fieldProps("consent")}
          type="checkbox"
          required
          checked={values.consent}
          onChange={(e) => update("consent", e.target.checked)}
        />
        <label htmlFor={id("consent")}>
          Соглашаюсь на обработку персональных данных в соответствии с{" "}
          <Link href="/privacy" target="_blank">
            политикой конфиденциальности
          </Link>
        </label>
      </div>
      {errors.consent && (
        <p className="field-error" id={id("consent-error")} style={{ marginTop: -12, marginBottom: 20 }}>
          {errors.consent}
        </p>
      )}

      <button
        className="btn btn-primary"
        type="submit"
        disabled={submitting}
        style={{ width: "100%", justifyContent: "center" }}
      >
        {submitting ? "Отправляю…" : "Отправить заявку"}
      </button>

      <div className={`form-status${status.kind === "error" ? " error" : ""}`} role="alert">
        {status.kind === "error" ? status.message : ""}
      </div>
    </form>
  );
}

function describeError(
  err: unknown,
  setErrors: (e: Errors) => void,
  focusFirstError: (e: Errors) => void,
): string {
  const fallback = `Не удалось отправить заявку. Попробуйте ещё раз или напишите в Telegram @${site.telegram.handle}.`;
  if (err instanceof NetworkError) {
    return `Нет связи с сервером. Проверьте подключение и попробуйте ещё раз — или напишите в Telegram @${site.telegram.handle}.`;
  }
  if (err instanceof ApiError) {
    if (err.status === 422 && err.body?.fields) {
      const fieldErrors: Errors = {};
      for (const f of FIELD_ORDER) if (err.body.fields[f]) fieldErrors[f] = err.body.fields[f];
      if (Object.keys(fieldErrors).length > 0) {
        setErrors(fieldErrors);
        focusFirstError(fieldErrors);
        return "Проверьте выделенные поля.";
      }
    }
    if (err.status === 429 && err.body?.message) return err.body.message;
  }
  return fallback;
}
