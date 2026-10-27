export type ImageSource = {
  format: "avif" | "webp" | "jpeg";
  width: number;
  height: number;
  url: string;
};

export type Photo = {
  slug: string;
  /** Номер кадра на контрольном листе: 01A, 02A, ... */
  frame: string;
  title: string;
  altText: string;
  category: string;
  technicalCaption: string;
  width?: number;
  height?: number;
  placeholder?: string;
  /** Пустой массив — фото ещё не загружено, показывается заглушка. */
  sources: ImageSource[];
};

export type PhotoCategory = {
  slug: string;
  title: string;
  description: string;
};

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
