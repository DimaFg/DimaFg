import Link from "next/link";

import { formatPrice } from "@/features/services/model/format";
import type { Service } from "@/features/services/model/types";

export function ServiceCard({ service, wide = false }: { service: Service; wide?: boolean }) {
  return (
    <li className={`service-card${wide ? " wide" : ""}`}>
      <span className="service-num mono" aria-hidden="true">
        {service.number}
      </span>
      <h3>
        <Link href={`/services/${service.slug}`} data-analytics="service_view">
          {service.title}
        </Link>
      </h3>
      <p>{service.summary}</p>
      <div className="service-price">
        <span>{formatPrice(service)}</span>
        <span className="service-more" aria-hidden="true">
          Подробнее →
        </span>
      </div>
    </li>
  );
}
