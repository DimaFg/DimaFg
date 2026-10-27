import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ContactSection } from "@/components/ContactSection";
import { JsonLd } from "@/components/JsonLd";
import { PageHero } from "@/components/PageHero";
import { Portfolio } from "@/components/Portfolio";
import { site } from "@/config/site";
import { categories, getCategory, photosByCategory } from "@/content/portfolio";
import { getService, services } from "@/content/services";

export function generateStaticParams() {
  return services.map((s) => ({ slug: s.slug }));
}

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const service = getService((await params).slug);
  if (!service) return {};
  const url = `/services/${service.slug}`;
  const title = service.seoTitle ?? service.title;
  const description = service.seoDescription ?? service.summary;
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: { url, title, description },
  };
}

export default async function ServicePage({ params }: Props) {
  const service = getService((await params).slug);
  if (!service) notFound();
  const category = service.portfolioCategory ? getCategory(service.portfolioCategory) : undefined;
  const examples = category ? photosByCategory(category.slug) : [];

  return (
    <>
      <PageHero
        eyebrow={`Услуга ${service.number}`}
        title={service.title}
        lead={service.summary}
        breadcrumbs={[
          { href: "/services", label: "Услуги" },
          { href: `/services/${service.slug}`, label: service.title },
        ]}
      />
      <section aria-label="Условия">
        <div className="service-detail">
          <div className="service-detail-body">
            <p>{service.summary}</p>
            <p>
              Напишите, что и где хотите снять, — отвечу {site.responseTime} и предложу формат и
              время. <Link href="#contact">Перейти к форме</Link>
            </p>
          </div>
          <dl className="service-facts">
            <div>
              <dt>Стоимость</dt>
              <dd>{service.priceText}</dd>
            </div>
            {service.durationText && (
              <div>
                <dt>Формат</dt>
                <dd>{service.durationText}</dd>
              </div>
            )}
            <div>
              <dt>География</dt>
              <dd>{site.region}</dd>
            </div>
          </dl>
        </div>
      </section>
      {category && examples.length > 0 && (
        <Portfolio
          photos={examples}
          categories={categories}
          filterMode="links"
          activeCategory={category.slug}
          eyebrow="Примеры работ"
          title={category.title}
        />
      )}
      <ContactSection services={services} defaultService={service.slug} title="Заявка на съёмку" />
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "Service",
          name: service.title,
          description: service.summary,
          url: `${site.url}/services/${service.slug}`,
          areaServed: site.region,
          provider: { "@type": "Person", name: site.photographerName, url: site.url },
        }}
      />
    </>
  );
}
