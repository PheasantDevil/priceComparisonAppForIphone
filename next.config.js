/** @type {import('next').NextConfig} */
const nextConfig = {
  // This is a placeholder config for Vercel
  // The actual frontend is in the frontend directory
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
