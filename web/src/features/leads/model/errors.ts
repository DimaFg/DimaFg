import { site } from "@/config/site";
import { ApiError, NetworkError } from "../api/leads";
import { FIELD_ORDER, type Errors } from "./form";

export function describeError(err: unknown): { message: string; fields: Errors } {
  const fallback = `Не удалось отправить заявку. Попробуйте ещё раз или напишите в Telegram @${site.telegram.handle}.`;
  if (err instanceof NetworkError) {
    return { fields: {}, message: `Нет связи с сервером. Проверьте подключение и попробуйте ещё раз — или напишите в Telegram @${site.telegram.handle}.` };
  }
  if (err instanceof ApiError) {
    if (err.status === 422 && err.body?.fields) {
      const fieldErrors: Errors = {};
      for (const f of FIELD_ORDER) if (err.body.fields[f]) fieldErrors[f] = err.body.fields[f];
      if (Object.keys(fieldErrors).length > 0) {
        return { fields: fieldErrors, message: "Проверьте выделенные поля." };
      }
    }
    if (err.status === 429 && err.body?.message) return { fields: {}, message: err.body.message };
  }
  return { fields: {}, message: fallback };
}
