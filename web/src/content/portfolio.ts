import type { Photo, PhotoCategory } from "@/lib/types";

// Совпадают с api/app/seed/data.json.
export const categories: PhotoCategory[] = [
  {
    slug: "street",
    title: "Стрит",
    description:
      "Город без постановки: архитектура, свет заката и человек, который растворяется в пространстве.",
  },
  {
    slug: "event",
    title: "Мероприятия",
    description: "Свадьбы, праздники и конференции — живые моменты без расстановки людей.",
  },
  {
    slug: "personal",
    title: "Личные фотосеты",
    description: "Портреты в городской среде — человек в пространстве, а не на его фоне.",
  },
  {
    slug: "student",
    title: "Для студентов",
    description: "Выпускные, портфолио и учебные проекты.",
  },
];

// Тестовые кадры из прототипа. Пустой sources — на месте фото показывается заглушка.
export const photos: Photo[] = [
  { slug: "tverskaya-0740", frame: "01A", title: "Тверская, утро", altText: "Тверская улица ранним утром", category: "street", technicalCaption: "Тверская, 07:40 · 35mm f/2", sources: [] },
  { slug: "metro-1812", frame: "02A", title: "Метро", altText: "Пассажиры на станции метро вечером", category: "street", technicalCaption: "Метро, 18:12 · 50mm f/1.8", sources: [] },
  { slug: "wedding-toast", frame: "03A", title: "Свадьба, тост", altText: "Гости поднимают бокалы на свадьбе", category: "event", technicalCaption: "Свадьба, тост · 24mm f/2.8", sources: [] },
  { slug: "courtyard-portrait", frame: "04A", title: "Портрет во дворе", altText: "Портрет девушки в московском дворе", category: "personal", technicalCaption: "Портрет, двор · 50mm f/1.8", sources: [] },
  { slug: "bridge-sunset", frame: "05A", title: "Мост на закате", altText: "Мост в контровом закатном свете", category: "street", technicalCaption: "Мост, закат · 35mm f/5.6", sources: [] },
  { slug: "graduation-campus", frame: "06A", title: "Выпускной", altText: "Выпускники во дворе кампуса", category: "student", technicalCaption: "Выпускной, кампус · 35mm f/2", sources: [] },
  { slug: "conference-lobby", frame: "07A", title: "Конференция", altText: "Участники конференции беседуют в кулуарах", category: "event", technicalCaption: "Конференция, кулуары · 35mm f/2.8", sources: [] },
  { slug: "rooftop-portrait", frame: "08A", title: "Портрет на крыше", altText: "Портрет на крыше в закатном свете", category: "personal", technicalCaption: "Портрет на крыше, закат · 50mm f/2", sources: [] },
];

export function getCategory(slug: string): PhotoCategory | undefined {
  return categories.find((c) => c.slug === slug);
}

export function photosByCategory(slug: string): Photo[] {
  return photos.filter((p) => p.category === slug);
}
