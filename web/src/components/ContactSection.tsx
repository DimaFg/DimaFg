import type { Service } from "@/lib/types";
import { ContactInformation } from "./ContactInformation";
import { LeadForm } from "./LeadForm";
import { Reveal } from "./Reveal";

type Props = {
  services: Service[];
  defaultService?: string;
  title?: string;
  headingLevel?: 1 | 2;
};

export function ContactSection({ services, defaultService, title = "Обсудим съёмку", headingLevel = 2 }: Props) {
  const Heading = headingLevel === 1 ? "h1" : "h2";
  return (
    <section id="contact" aria-labelledby="contact-title">
      <Reveal>
        <div className="eyebrow">Контакты</div>
        <Heading id="contact-title" className="section-title">
          {title}
        </Heading>
      </Reveal>
      <Reveal className="contact-wrap">
        <LeadForm services={services} defaultService={defaultService} />
        <ContactInformation />
      </Reveal>
    </section>
  );
}
