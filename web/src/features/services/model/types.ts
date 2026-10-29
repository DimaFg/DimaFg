export type Service = {
  slug: string;
  number: string;
  title: string;
  summary: string;
  priceText: string;
  durationText?: string;
  /** Название в селекте формы, если отличается от заголовка. */
  formLabel: string;
  /** Категория портфолио с примерами работ. */
  portfolioCategory?: string;
  seoTitle?: string;
  seoDescription?: string;
};
