import Link from "next/link";

export default function NotFound() {
  return (
    <section className="not-found">
      <div className="eyebrow">Ошибка 404</div>
      <h1>Кадр не найден</h1>
      <p>Такой страницы нет — возможно, плёнку засветили. Вернитесь к контрольному листу.</p>
      <div className="hero-cta" style={{ marginTop: 0 }}>
        <Link href="/" className="btn btn-primary">
          На главную
        </Link>
        <Link href="/portfolio" className="btn btn-ghost">
          Портфолио
        </Link>
      </div>
    </section>
  );
}
