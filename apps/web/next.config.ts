import type { NextConfig } from "next";

const config: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  // Public source revision, captured during the Netlify Git build (never a credential).
  env: { NEXT_PUBLIC_BUILD_REVISION: process.env.COMMIT_REF || "local" },
  async headers() {
    return [{ source: "/:path*", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "X-Robots-Tag", value: "noindex, nofollow" },
      // Keep the same-origin design gallery usable, but block clickjacking by other sites.
      { key: "Content-Security-Policy", value: "frame-ancestors 'self'; base-uri 'self'; object-src 'none'; form-action 'self'" },
      { key: "X-Frame-Options", value: "SAMEORIGIN" },
      // Dictation is an explicit first-party feature; it must remain available here.
      { key: "Permissions-Policy", value: "camera=(), geolocation=(), microphone=(self)" },
    ] }];
  },
};

export default config;
