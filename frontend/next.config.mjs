/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    // Local/E2E same-origin API proxy (production uses nginx instead).
    const backend = process.env.SKLAB_BACKEND_URL || "";
    if (!backend) return [];
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "no-referrer" },
          {
            key: "Content-Security-Policy",
            // Next.js App Router hydrates via first-party inline bootstrap
            // scripts; React's default escaping + text-only rendering remain
            // the XSS defense (covered by tests). object-src/frame-ancestors
            // stay locked down.
            value:
              "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
              + "img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'",
          },
        ],
      },
    ];
  },
};
export default nextConfig;
