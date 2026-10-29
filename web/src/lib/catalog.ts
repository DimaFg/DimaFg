import "server-only";

// Единая точка чтения публичного каталога для страниц, metadata и sitemap.
// Пока используем прежние демонстрационные данные: API ещё не содержит полного портфолио.
// Будущий адаптер API должен возвращать эти же модели представления.
import {
  categories,
  getCategory,
  photos,
  photosByCategory,
} from "@/features/portfolio/data/demo";
import { getService, services } from "@/features/services/data/demo";

export const catalog = { categories, photos, services, getCategory, getService, photosByCategory };
