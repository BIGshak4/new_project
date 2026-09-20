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
    ] }];
  },
};

export default config;
