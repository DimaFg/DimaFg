"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { Photo, PhotoCategory } from "@/lib/types";
import { BlankFrame, PhotoCard } from "./PhotoCard";
import { PhotoLightbox } from "./PhotoLightbox";
import { ALL, PortfolioFilters } from "./PortfolioFilters";
import { Reveal } from "./Reveal";

const COLUMNS = 3;

type Props = {
  photos: Photo[];
  categories: PhotoCategory[];
  /** buttons — фильтр на месте (главная); links — переход на страницы категорий. */
  filterMode: "buttons" | "links";
  activeCategory?: string;
  eyebrow?: string;
  title?: string;
  /** На внутренних страницах заголовок уже есть в шапке страницы. */
  showHeading?: boolean;
  showAllLink?: boolean;
};

export function Portfolio({
  photos,
  categories,
  filterMode,
  activeCategory = ALL,
  eyebrow = "Контрольный лист",
  title = "Избранные кадры",
  showHeading = true,
  showAllLink = false,
}: Props) {
  const [filter, setFilter] = useState(activeCategory);
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const visible = useMemo(
    () => (filterMode === "buttons" && filter !== ALL ? photos.filter((p) => p.category === filter) : photos),
    [photos, filter, filterMode],
  );
  // Пустые кадры добивают последний ряд контрольного листа, как в прототипе.
  const blanks = (COLUMNS - (visible.length % COLUMNS)) % COLUMNS;

  return (
    <section id="gallery" aria-labelledby={showHeading ? "gallery-title" : undefined} aria-label={showHeading ? undefined : title}>
      {showHeading && (
        <Reveal className="sheet-head">
          <div>
            <div className="eyebrow">{eyebrow}</div>
            <h2 id="gallery-title" className="section-title">
              {title}
            </h2>
          </div>
          <div className="mono" aria-hidden="true">
            <span className="sheet-hint-hover">НАВЕДИТЕ, ЧТОБЫ ОТМЕТИТЬ СЕЛЕКТ</span>
            <span className="sheet-hint-touch">НАЖМИТЕ НА КАДР, ЧТОБЫ ОТКРЫТЬ</span>
          </div>
        </Reveal>
      )}

      <Reveal>
        {filterMode === "buttons" ? (
          <PortfolioFilters mode="buttons" categories={categories} active={filter} onChange={setFilter} />
        ) : (
          <PortfolioFilters mode="links" categories={categories} active={activeCategory} />
        )}
      </Reveal>

      <p className="visually-hidden" aria-live="polite">
        Показано кадров: {visible.length}
      </p>

      <Reveal>
        {visible.length === 0 ? (
          <p className="sheet-empty">В этой категории пока нет опубликованных кадров.</p>
        ) : (
          <ul className="contact-sheet">
            {visible.map((photo, i) => (
              <li key={photo.slug}>
                <PhotoCard photo={photo} onOpen={() => setOpenIndex(i)} />
              </li>
            ))}
            {Array.from({ length: blanks }, (_, i) => (
              <li key={`blank-${i}`} aria-hidden="true">
                <BlankFrame />
              </li>
            ))}
          </ul>
        )}
      </Reveal>

      {showAllLink && (
        <div className="sheet-more">
          <Link href="/portfolio" className="btn btn-ghost">
            Всё портфолио <span aria-hidden="true">→</span>
          </Link>
        </div>
      )}

      <PhotoLightbox
        photos={visible}
        index={openIndex}
        onIndexChange={setOpenIndex}
        onClose={() => setOpenIndex(null)}
      />
    </section>
  );
}
