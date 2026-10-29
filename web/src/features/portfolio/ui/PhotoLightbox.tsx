"use client";

import { useEffect, useRef } from "react";

import type { Photo } from "@/features/portfolio/model/types";
import { PhotoImage } from "./PhotoImage";

type Props = {
  photos: Photo[];
  index: number | null;
  onIndexChange: (index: number) => void;
  onClose: () => void;
};

/**
 * Нативный <dialog> в модальном режиме: браузер сам делает фон inert, удерживает фокус,
 * закрывает по Escape и возвращает фокус на кнопку, открывшую диалог.
 */
export function PhotoLightbox({ photos, index, onIndexChange, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const open = index !== null && photos.length > 0;
  const photo = open ? photos[Math.min(index, photos.length - 1)] : null;
  const position = open ? Math.min(index, photos.length - 1) : 0;

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const go = (delta: number) => {
    if (!open) return;
    onIndexChange((position + delta + photos.length) % photos.length);
  };

  return (
    <dialog
      ref={ref}
      className="lightbox"
      aria-labelledby="lightbox-title"
      onClose={onClose}
      onClick={(e) => {
        // Клик по свободному полю диалога (не по кадру и не по кнопкам) закрывает его.
        const target = e.target as HTMLElement;
        if (target === e.currentTarget || target.classList.contains("lightbox-stage") || target.classList.contains("lightbox-figure")) {
          ref.current?.close();
        }
      }}
      onKeyDown={(e) => {
        if (e.key === "ArrowRight") go(1);
        if (e.key === "ArrowLeft") go(-1);
      }}
    >
      {photo && (
        <>
          <div className="lightbox-bar">
            <span aria-live="polite">
              Кадр {photo.frame} · {String(position + 1).padStart(2, "0")} /{" "}
              {String(photos.length).padStart(2, "0")}
            </span>
            <button type="button" className="lightbox-btn" onClick={() => ref.current?.close()} autoFocus>
              Закрыть <span aria-hidden="true">&nbsp;✕</span>
            </button>
          </div>

          <div className="lightbox-stage">
            <button
              type="button"
              className="lightbox-btn prev"
              onClick={() => go(-1)}
              aria-label="Предыдущий кадр"
              disabled={photos.length < 2}
            >
              ←
            </button>
            <figure className="lightbox-figure">
              {photo.sources.length > 0 ? (
                <PhotoImage photo={photo} sizes="100vw" priority />
              ) : (
                <div className="lightbox-placeholder" role="img" aria-label={photo.altText}>
                  ЗАМЕНИТЕ НА ФОТО
                </div>
              )}
            </figure>
            <button
              type="button"
              className="lightbox-btn next"
              onClick={() => go(1)}
              aria-label="Следующий кадр"
              disabled={photos.length < 2}
            >
              →
            </button>
          </div>

          <div className="lightbox-caption">
            <h2 id="lightbox-title">{photo.title}</h2>
            <p>{photo.technicalCaption}</p>
          </div>
        </>
      )}
    </dialog>
  );
}
