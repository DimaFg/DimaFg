import { site } from "@/config/site";
import type { components } from "@/lib/api/schema";

export type LeadCreate = components["schemas"]["LeadCreate"];
export type LeadCreated = components["schemas"]["LeadCreated"];
export type ApiErrorBody = components["schemas"]["ErrorBody"];

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiErrorBody | null,
  ) {
    super(body?.message ?? `HTTP ${status}`);
  }
}

export class NetworkError extends Error {}

export async function submitLead(
  payload: LeadCreate,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<LeadCreated> {
  let response: Response;
  try {
    response = await fetch(`${site.apiBaseUrl}/api/v1/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new NetworkError("network");
  }
  if (response.ok) return (await response.json()) as LeadCreated;

  let body: ApiErrorBody | null = null;
  try {
    body = ((await response.json()) as { error?: ApiErrorBody }).error ?? null;
  } catch {
    // ответ не JSON (например, 502 от прокси)
  }
  throw new ApiError(response.status, body);
}
