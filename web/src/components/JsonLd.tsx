/** Структурированные данные schema.org. Разметка должна совпадать с видимым содержимым страницы. */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      // JSON.stringify не экранирует "</script>" — заменяем "<" на безопасную последовательность.
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}
