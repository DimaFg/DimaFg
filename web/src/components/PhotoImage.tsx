import type { Photo } from "@/lib/types";

const FORMAT_ORDER = ["avif", "webp"] as const;
const MIME = { avif: "image/avif", webp: "image/webp", jpeg: "image/jpeg" } as const;

function srcSet(photo: Photo, format: keyof typeof MIME): string {
  return photo.sources
    .filter((s) => s.format === format)
    .map((s) => `${s.url} ${s.width}w`)
    .join(", ");
}

type Props = {
  photo: Photo;
  sizes: string;
  className?: string;
  priority?: boolean;
};

/** <picture> с AVIF/WebP и JPEG fallback. Возвращает null, если фото ещё не загружено. */
export function PhotoImage({ photo, sizes, className, priority = false }: Props) {
  if (photo.sources.length === 0) return null;
  const jpeg = photo.sources.filter((s) => s.format === "jpeg");
  const fallback = (jpeg.length ? jpeg : photo.sources).at(-1)!;
  return (
    <picture>
      {FORMAT_ORDER.map((format) => {
        const set = srcSet(photo, format);
        return set ? <source key={format} type={MIME[format]} srcSet={set} sizes={sizes} /> : null;
      })}
      <img
        className={className}
        src={fallback.url}
        srcSet={srcSet(photo, "jpeg") || undefined}
        sizes={sizes}
        alt={photo.altText}
        width={photo.width ?? fallback.width}
        height={photo.height ?? fallback.height}
        loading={priority ? "eager" : "lazy"}
        fetchPriority={priority ? "high" : "auto"}
        decoding="async"
        style={photo.placeholder ? { backgroundImage: `url(${photo.placeholder})` } : undefined}
      />
    </picture>
  );
}
