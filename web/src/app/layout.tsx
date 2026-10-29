import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Inter, Oswald } from "next/font/google";

import { AttributionCapture } from "@/features/leads/ui/AttributionCapture";
import { FilmChrome } from "@/components/layout/FilmChrome";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { isProduction, site } from "@/config/site";

import "@/styles/base.css";
import "@/components/layout/header.css";
import "@/components/home/hero.css";
import "@/components/home/about.css";
import "@/components/home/statement.css";
import "@/features/portfolio/ui/portfolio.css";
import "@/features/portfolio/ui/lightbox.css";
import "@/features/services/ui/services.css";
import "@/features/leads/ui/contact.css";
import "@/components/layout/footer.css";
import "@/styles/pages.css";

const oswald = Oswald({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-oswald",
  display: "swap",
});
const inter = Inter({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600"],
  variable: "--font-inter",
  display: "swap",
});
const plexMono = IBM_Plex_Mono({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: { default: site.name, template: `%s — ${site.name}` },
  description: site.description,
  applicationName: site.name,
  robots: isProduction ? undefined : { index: false, follow: false },
  openGraph: {
    type: "website",
    locale: site.locale,
    siteName: site.name,
    title: site.name,
    description: site.description,
    url: "/",
  },
  alternates: { canonical: "/" },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  themeColor: "#141210",
  colorScheme: "dark",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru" className={`${oswald.variable} ${inter.variable} ${plexMono.variable}`}>
      <body>
        <noscript>
          <style>{".reveal{opacity:1!important;transform:none!important}"}</style>
        </noscript>
        <a href="#main" className="skip-link">
          Перейти к содержимому
        </a>
        <FilmChrome />
        <div className="frame">
          <Header />
          <main id="main">{children}</main>
          <Footer />
        </div>
        <AttributionCapture />
      </body>
    </html>
  );
}
