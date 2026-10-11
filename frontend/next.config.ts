import path from "path";
import { fileURLToPath } from "url";

import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
loadEnvConfig(rootDir);

const nextConfig: NextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

export default nextConfig;
