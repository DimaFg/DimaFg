import Link from "next/link";

import { site } from "@/config/site";

export function Footer() {
  return (
    <footer className="site-footer">
      <span>
        © {site.copyrightYear} {site.photographerName} · уличная фотография
      </span>
      <nav className="footer-links" aria-label="Служебные ссылки">
        <Link href="/portfolio">Портфолио</Link>
        <Link href="/services">Услуги</Link>
        <Link href="/privacy">Политика конфиденциальности</Link>
      </nav>
      <span>Сайт — контрольный лист вашего города</span>
    </footer>
  );
}
