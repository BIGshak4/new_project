import type { NextConfig } from "next";

const config: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  ...(process.env.JOBRUN_SELF_HOSTED === "1" ? { output: "standalone" as const } : {}),
  // Public source revision from the hosting provider (never a credential).
  env: { NEXT_PUBLIC_BUILD_REVISION: process.env.SOURCE_REVISION || process.env.COMMIT_REF || process.env.VERCEL_GIT_COMMIT_SHA || "local" },
  async headers() {
    return [{ source: "/:path*", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "X-Robots-Tag", value: "noindex, nofollow" },
      { key: "Content-Security-Policy", value: "frame-ancestors 'self'; base-uri 'self'; object-src 'none'; form-action 'self'" },
      { key: "X-Frame-Options", value: "SAMEORIGIN" },
      { key: "Permissions-Policy", value: "camera=(), geolocation=(), microphone=()" },
    ] }];
  },
};

export default config;
