/** Плёночное зерно и тёмные полосы по краям, как в прототипе. Декор скрыт от скринридеров. */
export function FilmChrome() {
  return (
    <>
      <div className="grain" aria-hidden="true" />
      <div className="rail left" aria-hidden="true" />
      <div className="rail right" aria-hidden="true" />
    </>
  );
}
