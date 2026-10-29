import type { Service } from "@/features/services/model/types";
import { Reveal } from "@/shared/ui/Reveal";
import { ServiceCard } from "./ServiceCard";

type Props = { services: Service[]; showHeading?: boolean };

export function Services({ services, showHeading = true }: Props) {
  // Нечётная последняя карточка растягивается на всю ширину, как седьмая в прототипе.
  const lastIsWide = services.length % 2 === 1;
  return (
    <section id="services" aria-labelledby={showHeading ? "services-title" : undefined} aria-label={showHeading ? undefined : "Список услуг"}>
      {showHeading && (
        <Reveal>
          <div className="eyebrow">Услуги</div>
          <h2 id="services-title" className="section-title">
            Чем могу быть полезен
          </h2>
        </Reveal>
      )}
      <Reveal as="ul" className="services-grid">
        {services.map((s, i) => (
          <ServiceCard key={s.slug} service={s} wide={lastIsWide && i === services.length - 1} />
        ))}
      </Reveal>
    </section>
  );
}
