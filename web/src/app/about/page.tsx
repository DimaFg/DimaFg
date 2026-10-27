import type { Metadata } from "next";

import { About } from "@/components/About";
import { ArtistStatement } from "@/components/ArtistStatement";

export const metadata: Metadata = {
  title: "О фотографе",
  description: "Уличный фотограф: подход к кадру, визуальный язык и темы — монументальность с трещинами.",
  alternates: { canonical: "/about" },
  openGraph: { url: "/about" },
};

export default function AboutPage() {
  return (
    <div style={{ paddingTop: 60 }}>
      <About headingLevel={1} />
      <ArtistStatement />
    </div>
  );
}
