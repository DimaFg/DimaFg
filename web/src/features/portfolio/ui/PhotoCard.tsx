import type { Photo } from "@/features/portfolio/model/types";
import { PhotoImage } from "./PhotoImage";

const SIZES = "(max-width: 700px) 50vw, (max-width: 1180px) 33vw, 380px";

type Props = {
  photo: Photo;
  onOpen: () => void;
};

export function PhotoCard({ photo, onOpen }: Props) {
  const hasImage = photo.sources.length > 0;
  return (
    <button
      type="button"
      className="frame-cell"
      aria-label={`Открыть кадр ${photo.frame}: ${photo.title}`}
      aria-haspopup="dialog"
      onClick={onOpen}
    >
      <span className="frame-num mono" aria-hidden="true">
        {photo.frame}
      </span>
      {hasImage ? (
        <PhotoImage photo={photo} sizes={SIZES} className="ph" />
      ) : (
        <span className="ph" aria-hidden="true">
          <span className="ph-label">
            ЗАМЕНИТЕ
            <br />
            НА ФОТО
          </span>
        </span>
      )}
      <span className="select-mark" aria-hidden="true" />
      <span className="frame-cap" aria-hidden="true">
        {photo.technicalCaption}
      </span>
    </button>
  );
}

export function BlankFrame() {
  return (
    <div className="frame-blank" aria-hidden="true">
      <span className="frame-num mono">—</span>
      <span className="ph">
        <span className="ph-label mono">
          ПУСТОЙ
          <br />
          КАДР
        </span>
      </span>
    </div>
  );
}
