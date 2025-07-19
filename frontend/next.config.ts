import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Vercel最適化
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['react-icons', 'recharts'],
  },
  // 環境変数
  env: {
    BACKEND_URL:
      process.env.BACKEND_URL ||
      'https://price-comparison-app-asia-northeast1.run.app',
  },
  // ビルドエラーを無視
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // バンドル分析
  webpack: (config, { isServer, dev }) => {
    if (!isServer && !dev && process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
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
