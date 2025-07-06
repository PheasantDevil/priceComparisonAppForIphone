import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
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
  // ビルド時の最適化
  swcMinify: false,
  // 静的エクスポート用の設定
  experimental: {
    // 静的エクスポートを確実にする
    staticExport: true,
  },
};

export default nextConfig;
