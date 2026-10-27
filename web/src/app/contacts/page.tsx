import type { Metadata } from "next";

import { ContactSection } from "@/components/ContactSection";
import { site } from "@/config/site";
import { services } from "@/content/services";

export const metadata: Metadata = {
  title: "Контакты",
  description: `Заявка на съёмку, Telegram и почта. ${site.region}, ответ ${site.responseTime}.`,
  alternates: { canonical: "/contacts" },
  openGraph: { url: "/contacts" },
};

export default function ContactsPage() {
  return (
    <div style={{ paddingTop: 60 }}>
      <ContactSection services={services} headingLevel={1} />
    </div>
  );
}
