import { About } from "@/components/About";
import { ArtistStatement } from "@/components/ArtistStatement";
import { ContactSection } from "@/components/ContactSection";
import { Hero } from "@/components/Hero";
import { JsonLd } from "@/components/JsonLd";
import { Portfolio } from "@/components/Portfolio";
import { Services } from "@/components/Services";
import { site } from "@/config/site";
import { categories, photos } from "@/content/portfolio";
import { services } from "@/content/services";

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
