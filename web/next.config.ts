import type { NextConfig } from "next";

// В local/dev Next проксирует /api на FastAPI. В production /api обслуживает Caddy.
const apiInternalUrl = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  poweredByHeader: false,
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiInternalUrl}/api/:path*` }];
  },
};

export default nextConfig;
