import type { NextConfig } from "next";

// Static export: the admin web is a client-side app served from Cloudflare Pages
// (system design v2.3 §4.2.A); every data call goes to the FastAPI backend.
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
