import { about } from "@/content/about";
import { Reveal } from "@/shared/ui/Reveal";

export function About({ headingLevel = 2 }: { headingLevel?: 1 | 2 }) {
  const Heading = headingLevel === 1 ? "h1" : "h2";
  return (
    <section id="about" aria-labelledby="about-title">
      <Reveal className="about">
        <figure className={`about-portrait${about.portrait ? "" : " is-empty"}`}>
          {about.portrait && (
            // eslint-disable-next-line @next/next/no-img-element -- портрет придёт с CDN готовым srcset
            <img
              src={about.portrait.src}
              alt={about.portrait.alt}
              width={about.portrait.width}
              height={about.portrait.height}
              loading="lazy"
              decoding="async"
            />
          )}
          <figcaption className="corner-tag mono" aria-hidden="true">
            FRAME 00 / PORTRAIT
          </figcaption>
        </figure>
        <div className="about-body">
          <div className="eyebrow">О фотографе</div>
          <Heading id="about-title" className="section-title">
            {about.title}
          </Heading>
          <p>{about.paragraphs[0]}</p>
          <blockquote className="about-quote">{about.quote}</blockquote>
          <p>{about.paragraphs[1]}</p>
          <dl className="about-stats">
            {about.stats.map((s) => (
              <div key={s.label}>
                <dt>{s.label}</dt>
                <dd>{s.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Reveal>
    </section>
  );
}
