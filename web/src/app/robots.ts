import type { MetadataRoute } from "next";

import { isProduction, site } from "@/config/site";

export default function robots(): MetadataRoute.Robots {
  if (!isProduction) {
    // staging и local не должны попадать в поиск
    return { rules: { userAgent: "*", disallow: "/" } };
  }
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/admin", "/api/"] },
    sitemap: `${site.url}/sitemap.xml`,
    host: site.url,
  };
}
