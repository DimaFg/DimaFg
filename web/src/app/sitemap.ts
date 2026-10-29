import type { MetadataRoute } from "next";

import { site } from "@/config/site";
import { catalog } from "@/lib/catalog";

const { categories, photos, services } = catalog;

export default function sitemap(): MetadataRoute.Sitemap {
  const url = (path: string) => `${site.url}${path}`;
  // Карта изображений: только реально опубликованные файлы с CDN.
  const imagesFor = (category?: string) =>
    photos
      .filter((p) => p.sources.length > 0 && (!category || p.category === category))
      .map((p) => p.sources.at(-1)!.url);

  return [
    { url: url("/"), changeFrequency: "monthly", priority: 1, images: imagesFor() },
    { url: url("/portfolio"), changeFrequency: "weekly", priority: 0.9, images: imagesFor() },
    ...categories.map((c) => ({
      url: url(`/portfolio/${c.slug}`),
      changeFrequency: "weekly" as const,
      priority: 0.8,
      images: imagesFor(c.slug),
    })),
    { url: url("/services"), changeFrequency: "monthly", priority: 0.9 },
    ...services.map((s) => ({
      url: url(`/services/${s.slug}`),
      changeFrequency: "monthly" as const,
      priority: 0.8,
    })),
    { url: url("/about"), changeFrequency: "yearly", priority: 0.6 },
    { url: url("/contacts"), changeFrequency: "yearly", priority: 0.7 },
    { url: url("/privacy"), changeFrequency: "yearly", priority: 0.2 },
  ];
}
