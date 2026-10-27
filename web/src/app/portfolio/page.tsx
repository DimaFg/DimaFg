import type { Metadata } from "next";

import { PageHero } from "@/components/PageHero";
import { Portfolio } from "@/components/Portfolio";
import { categories, photos } from "@/content/portfolio";

export const metadata: Metadata = {
  title: "Портфолио",
  description: "Уличная фотография, мероприятия, личные фотосеты и студенческие съёмки — контрольный лист избранных кадров.",
  alternates: { canonical: "/portfolio" },
  openGraph: { url: "/portfolio" },
};

export default function PortfolioPage() {
  return (
    <>
      <PageHero
        eyebrow="Контрольный лист"
        title="Портфолио"
        lead="Город без постановки: архитектура, закатный свет и люди, которые растворяются в пространстве."
        breadcrumbs={[{ href: "/portfolio", label: "Портфолио" }]}
      />
      <Portfolio photos={photos} categories={categories} filterMode="links" showHeading={false} title="Все кадры" />
    </>
  );
}
