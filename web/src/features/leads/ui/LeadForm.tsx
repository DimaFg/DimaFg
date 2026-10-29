"use client";

import Link from "next/link";

import { LIMITS, type FieldName, type LeadServiceOption } from "../model/form";
import { useLeadForm } from "../model/useLeadForm";

type Props = { services: LeadServiceOption[]; defaultService?: string };

export function LeadForm({ services, defaultService }: Props) {
  const {
    values, errors, status, formRef, successRef, id, update, onSubmit, reset,
  } = useLeadForm(defaultService ?? services[0]?.slug ?? "other");

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
