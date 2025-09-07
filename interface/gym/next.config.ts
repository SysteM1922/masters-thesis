import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  env: {
    SERVICES_API_HOST: process.env.SERVICES_API_HOST,
    SERVICES_API_PORT: process.env.SERVICES_API_PORT,
    SIGNALING_SERVER_HOST: process.env.SIGNALING_SERVER_HOST,
    SIGNALING_SERVER_PORT: process.env.SIGNALING_SERVER_PORT,
    SERVER_ID: process.env.SERVER_ID,
    TURN_SERVER_HOST: process.env.TURN_SERVER_HOST,
    TURN_SERVER_PORT: process.env.TURN_SERVER_PORT,
    TURN_SERVER_USERNAME: process.env.TURN_SERVER_USERNAME,
    TURN_SERVER_CREDENTIAL: process.env.TURN_SERVER_CREDENTIAL
  }
};

export default nextConfig;
