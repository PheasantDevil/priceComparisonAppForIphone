import type { NextConfig } from 'next';
import { BundleAnalyzerPlugin } from 'webpack-bundle-analyzer';

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
    domains: ['storage.googleapis.com'],
  },
  // ビルドエラーを無視
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['react-icons', 'recharts'],
  },
  env: {
    BACKEND_URL:
      process.env.BACKEND_URL ||
      'https://price-comparison-app-asia-northeast1.run.app',
  },
  poweredByHeader: false,
  compress: true,
  webpack: (config, { isServer, dev }) => {
    if (!isServer && !dev && process.env.ANALYZE === 'true') {
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
        })
      );
    }
    return config;
  },
};

export default nextConfig;
