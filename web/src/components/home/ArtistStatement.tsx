import { statement } from "@/content/about";
import { Reveal } from "@/shared/ui/Reveal";

export function ArtistStatement() {
  return (
    <section id="statement" className="statement" aria-labelledby="statement-title">
      <div className="statement-glow" aria-hidden="true" />
      <Reveal className="statement-body">
        <div className="eyebrow">Декларация артиста</div>
        <h2 id="statement-title" className="section-title">
          {statement.title}
        </h2>
        <p className="statement-intro">{statement.intro}</p>

        <div className="statement-grid">
          {statement.blocks.map((b) => (
            <div key={b.label} className="statement-block">
              <h3 className="statement-label">{b.label}</h3>
              <p>{b.text}</p>
            </div>
          ))}
        </div>

        <p className="statement-pull">
          Моя миссия — находить <em>монументальность с трещинами</em>: там, где через разломы
          раскрывается то светлое, что спрятано глубоко внутри человека.
        </p>

        <ul className="values-list">
          {statement.values.map((v) => (
            <li key={v.title} className="value-item">
              <h3>{v.title}</h3>
              <p>{v.text}</p>
            </li>
          ))}
        </ul>
      </Reveal>
    </section>
  );
}
