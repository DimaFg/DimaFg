import type { Metadata } from "next";

import { ContactSection } from "@/components/ContactSection";
import { PageHero } from "@/components/PageHero";
import { Services } from "@/components/Services";
import { site } from "@/config/site";
import { services } from "@/content/services";

export const metadata: Metadata = {
  title: "Услуги и цены",
  description: `Съёмка мероприятий, личные фотосеты, фотопрогулки, съёмка для брендов и разбор кадров. ${site.region}.`,
  alternates: { canonical: "/services" },
  openGraph: { url: "/services" },
};

export default function ServicesPage() {
  return (
    <>
      <PageHero
        eyebrow="Услуги"
        title="Чем могу быть полезен"
        lead={`Съёмка без постановки и студийного глянца. ${site.region}.`}
        breadcrumbs={[{ href: "/services", label: "Услуги" }]}
      />
      <Services services={services} showHeading={false} />
      <ContactSection services={services} />
    </>
  );
}
