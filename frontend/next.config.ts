import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // ビルド最適化
  swcMinify: true,
  experimental: {
    optimizeCss: true,
  },
  // 不要な機能を無効化
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // 静的エクスポートの最適化
  distDir: 'out',
};

export default nextConfig;
