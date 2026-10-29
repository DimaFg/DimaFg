"use client";

import { type FormEvent, useEffect, useId, useRef, useState } from "react";

import { site } from "@/config/site";
import { submitLead } from "../api/leads";
import { getAttribution } from "./attribution";
import { describeError } from "./errors";
import { FIELD_ORDER, type Errors, type FieldName, type Status, type Values, validate } from "./form";
import { normalizeValues, resolveAttempt, type SubmissionAttempt } from "./submission";

export function useLeadForm(defaultService: string) {
  const initial: Values = {
    name: "",
    contact: "",
    service: defaultService,
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
  const attempt = useRef<SubmissionAttempt | null>(null);
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

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (inFlight.current) return;
    const clientErrors = validate(values);
    setErrors(clientErrors);
    if (Object.keys(clientErrors).length > 0) {
      setStatus({ kind: "idle" });
      focusFirstError(clientErrors);
      return;
    }

    attempt.current = resolveAttempt(attempt.current, values);
    inFlight.current = true;
    setStatus({ kind: "submitting" });
    try {
      const result = await submitLead(
        {
          ...normalizeValues(values),
          privacy_policy_version: site.privacyPolicyVersion,
          elapsed_ms: shownAt.current ? Date.now() - shownAt.current : null,
          attribution: getAttribution(),
        },
        attempt.current.key,
      );
      setStatus({ kind: "success", result });
    } catch (error) {
      const failure = describeError(error);
      setErrors(failure.fields);
      focusFirstError(failure.fields);
      setStatus({ kind: "error", message: failure.message });
    } finally {
      inFlight.current = false;
    }
  }

  function reset() {
    setValues({ ...initial, service: values.service });
    setErrors({});
    attempt.current = null;
    shownAt.current = Date.now();
    setStatus({ kind: "idle" });
  }

  return { values, errors, status, formRef, successRef, id, update, onSubmit, reset };
}
