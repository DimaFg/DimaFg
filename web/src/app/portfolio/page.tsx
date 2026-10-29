import type { Metadata } from "next";

import { PageHero } from "@/shared/ui/PageHero";
import { Portfolio } from "@/features/portfolio/ui/Portfolio";
import { catalog } from "@/lib/catalog";

const { categories, photos } = catalog;

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
