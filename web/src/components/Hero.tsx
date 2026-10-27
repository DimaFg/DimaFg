import Link from "next/link";

import { hero } from "@/content/about";

export function Hero() {
  return (
    <section className="hero" id="top" aria-labelledby="hero-title">
      <div className="hero-frame-tag mono" aria-hidden="true">
        <span>
          <span className="dot" />
          {hero.frameTag[0]}
        </span>
        <span>{hero.frameTag[1]}</span>
      </div>
      <h1 id="hero-title">
        Монументальность
        <br />с <em>трещинами</em>.
      </h1>
      <p>{hero.lead}</p>
      <div className="hero-cta">
        <Link href="/#gallery" className="btn btn-primary" data-analytics="cta_click">
          Смотреть контрольный лист
        </Link>
        <Link href="/#contact" className="btn btn-ghost" data-analytics="cta_click">
          Обсудить съёмку
        </Link>
      </div>
    </section>
  );
}
