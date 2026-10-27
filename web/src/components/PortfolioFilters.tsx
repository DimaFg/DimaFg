import Link from "next/link";

import type { PhotoCategory } from "@/lib/types";

export const ALL = "all";

type ButtonProps = {
  mode: "buttons";
  categories: PhotoCategory[];
  active: string;
  onChange: (slug: string) => void;
};

type LinkProps = {
  mode: "links";
  categories: PhotoCategory[];
  active: string;
};

/**
 * На главной фильтры — кнопки (aria-pressed), без перезагрузки и без прокрутки к началу.
 * На страницах /portfolio — ссылки на отдельные индексируемые URL категорий.
 */
export function PortfolioFilters(props: ButtonProps | LinkProps) {
  const items = [{ slug: ALL, title: "Все" }, ...props.categories];
  return (
    <ul className="sheet-filters" aria-label="Фильтр по типу съёмки">
      {items.map((c) => {
        const isActive = c.slug === props.active;
        const className = `filter-tab${isActive ? " active" : ""}`;
        return (
          <li key={c.slug}>
            {props.mode === "buttons" ? (
              <button
                type="button"
                className={className}
                aria-pressed={isActive}
                onClick={() => props.onChange(c.slug)}
              >
                {c.title}
              </button>
            ) : (
              <Link
                className={className}
                href={c.slug === ALL ? "/portfolio" : `/portfolio/${c.slug}`}
                aria-current={isActive ? "page" : undefined}
                scroll={false}
              >
                {c.title}
              </Link>
            )}
          </li>
        );
      })}
    </ul>
  );
}
