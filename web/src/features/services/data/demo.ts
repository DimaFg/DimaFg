import type { Service } from "@/features/services/model/types";

// Тестовые данные из прототипа. Совпадают с api/app/seed/data.json; после запуска
// админки услуг страницы будут собираться из GET /api/v1/services.
export const services: Service[] = [
  {
    slug: "events",
    number: "01",
    title: "Съёмка мероприятий",
    formLabel: "Мероприятие",
    summary:
      "Свадьбы, дни рождения, конференции, городские события. Не расставляю людей — ловлю живую ткань момента, которая останется, когда декорации уберут.",
    priceText: "от 8 000 ₽",
    durationText: "до 3 часов",
    portfolioCategory: "event",
  },
  {
    slug: "personal",
    number: "02",
    title: "Личные фотосеты",
    formLabel: "Личный фотосет",
    summary:
      "Портретная съёмка в городской среде — без студийного глянца. В кадре вы существуете в пространстве, а не позируете на его фоне.",
    priceText: "от 5 000 ₽",
    durationText: "1.5 часа, 15–20 кадров",
    portfolioCategory: "personal",
  },
  {
    slug: "students",
    number: "03",
    title: "Съёмка для студентов",
    formLabel: "Для студентов",
    summary:
      "Выпускной, портфолио, проект для учёбы. Сам студент — понимаю бюджет и сроки, снимаю быстро и без лишнего пафоса.",
    priceText: "скидка 20% по студенческому билету",
    portfolioCategory: "student",
  },
  {
    slug: "photowalk",
    number: "04",
    title: "Фотопрогулка по городу",
    formLabel: "Фотопрогулка",
    summary:
      "Два часа съёмки вместе: показываю, как я ищу свет и момент, вы уходите с готовыми кадрами и новым взглядом на привычные улицы.",
    priceText: "от 4 500 ₽",
    durationText: "2 часа",
    portfolioCategory: "street",
  },
  {
    slug: "brand",
    number: "05",
    title: "Съёмка для бренда и соцсетей",
    formLabel: "Съёмка для бренда",
    summary:
      "Живые, неспостановочные кадры продукта или команды в городской среде — без глянцевой искусственности студийного света.",
    priceText: "от 12 000 ₽",
    durationText: "проект",
  },
  {
    slug: "consultation",
    number: "06",
    title: "Разбор и консультация",
    formLabel: "Разбор кадров",
    summary:
      "Присылаете подборку своих кадров — разбираю композицию, свет и монтаж серии, даю честную обратную связь.",
    priceText: "от 2 000 ₽",
    durationText: "серия",
  },
  {
    slug: "print",
    number: "07",
    title: "Печать и подборка кадров",
    formLabel: "Печать",
    summary:
      "Помогу отобрать и подготовить серию к печати — от контрольного листа до финальной обработки в Lightroom.",
    priceText: "по договорённости",
  },
];

export function getService(slug: string): Service | undefined {
  return services.find((s) => s.slug === slug);
}
