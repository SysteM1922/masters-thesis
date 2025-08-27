import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  env: {
    SERVICES_API_HOST: process.env.SERVICES_API_HOST,
    SERVICES_API_PORT: process.env.SERVICES_API_PORT,
    SIGNALING_SERVER_HOST: process.env.SIGNALING_SERVER_HOST,
    SIGNALING_SERVER_PORT: process.env.SIGNALING_SERVER_PORT
  }
};

export default nextConfig;
