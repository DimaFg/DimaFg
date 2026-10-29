import { About } from "@/components/home/About";
import { ArtistStatement } from "@/components/home/ArtistStatement";
import { ContactSection } from "@/features/leads/ui/ContactSection";
import { Hero } from "@/components/home/Hero";
import { JsonLd } from "@/shared/ui/JsonLd";
import { Portfolio } from "@/features/portfolio/ui/Portfolio";
import { Services } from "@/features/services/ui/Services";
import { site } from "@/config/site";
import { catalog } from "@/lib/catalog";

const { categories, photos, services } = catalog;

export default function HomePage() {
  return (
    <>
      <Hero />
      <About />
      <ArtistStatement />
      <Portfolio photos={photos} categories={categories} filterMode="buttons" showAllLink />
      <Services services={services} />
      <ContactSection services={services} />
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Person",
              "@id": `${site.url}/#person`,
              name: site.photographerName,
              jobTitle: "Фотограф",
              url: site.url,
              sameAs: [site.telegram.url],
            },
            {
              "@type": "ProfessionalService",
              "@id": `${site.url}/#service`,
              name: site.name,
              description: site.description,
              url: site.url,
              areaServed: site.region,
              email: site.email,
              founder: { "@id": `${site.url}/#person` },
            },
          ],
        }}
      />
    </>
  );
}
