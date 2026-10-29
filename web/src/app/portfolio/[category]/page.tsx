import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PageHero } from "@/shared/ui/PageHero";
import { Portfolio } from "@/features/portfolio/ui/Portfolio";
import { catalog } from "@/lib/catalog";

const { categories, getCategory, photosByCategory } = catalog;

export function generateStaticParams() {
  return categories.map((c) => ({ category: c.slug }));
}

type Props = { params: Promise<{ category: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const category = getCategory((await params).category);
  if (!category) return {};
  const url = `/portfolio/${category.slug}`;
  return {
    title: `${category.title} — портфолио`,
    description: category.description,
    alternates: { canonical: url },
    openGraph: { url, title: category.title, description: category.description },
  };
}

export default async function CategoryPage({ params }: Props) {
  const category = getCategory((await params).category);
  if (!category) notFound();
  return (
    <>
      <PageHero
        eyebrow="Портфолио"
        title={category.title}
        lead={category.description}
        breadcrumbs={[
          { href: "/portfolio", label: "Портфолио" },
          { href: `/portfolio/${category.slug}`, label: category.title },
        ]}
      />
      <Portfolio
        photos={photosByCategory(category.slug)}
        categories={categories}
        filterMode="links"
        activeCategory={category.slug}
        showHeading={false}
        title={category.title}
      />
    </>
  );
}
