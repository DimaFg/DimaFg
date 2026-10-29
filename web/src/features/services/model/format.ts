import type { Service } from "./types";

export function formatPrice(service: Service): string {
  return service.durationText ? `${service.priceText} / ${service.durationText}` : service.priceText;
}
