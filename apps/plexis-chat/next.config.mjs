/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        // Stop the RunPod proxy / browser from caching the HTML document,
        // so a redeploy is seen immediately. Hashed assets under
        // /_next/static keep their own long-lived immutable caching.
        source: "/",
        headers: [
          { key: "Cache-Control", value: "no-store, must-revalidate" },
        ],
      },
    ];
  },
};
export default nextConfig;
