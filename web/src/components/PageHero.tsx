import Link from "next/link";

import { site } from "@/config/site";
import { JsonLd } from "./JsonLd";

type Crumb = { href: string; label: string };

type Props = {
  eyebrow: string;
  title: string;
  lead?: string;
  breadcrumbs: Crumb[];
};

export function PageHero({ eyebrow, title, lead, breadcrumbs }: Props) {
  const trail = [{ href: "/", label: "Главная" }, ...breadcrumbs];
  return (
    <section className="page-hero" aria-labelledby="page-title">
      <nav className="breadcrumbs" aria-label="Навигационная цепочка">
        <ol>
          {trail.map((c, i) =>
            i === trail.length - 1 ? (
              <li key={c.href} aria-current="page">
                {c.label}
              </li>
            ) : (
              <li key={c.href}>
                <Link href={c.href}>{c.label}</Link>
              </li>
            ),
          )}
        </ol>
      </nav>
      <div className="eyebrow">{eyebrow}</div>
      <h1 id="page-title">{title}</h1>
      {lead && <p>{lead}</p>}
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          itemListElement: trail.map((c, i) => ({
            "@type": "ListItem",
            position: i + 1,
            name: c.label,
            item: `${site.url}${c.href}`,
          })),
        }}
      />
    </section>
  );
}
