import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
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
  // Vercel最適化
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['react-icons', 'recharts'],
  },
  // 静的エクスポート最適化
  distDir: 'out',
  // 環境変数
  env: {
    BACKEND_URL:
      process.env.BACKEND_URL ||
      'https://price-comparison-app-asia-northeast1.run.app',
  },
  // 静的エクスポート用の設定
  skipTrailingSlashRedirect: true,
  skipMiddlewareUrlNormalize: true,
  // 静的エクスポートを強制
  assetPrefix: '',
  basePath: '',
  // 静的エクスポートの最適化
  generateBuildId: async () => {
    return 'static-build';
  },
  // 静的エクスポートの設定
  exportPathMap: async function () {
    return {
      '/': { page: '/' },
      '/404': { page: '/404' },
    };
  },
  // Vercel用の設定
  poweredByHeader: false,
  compress: true,
  // 静的エクスポートを強制
  staticPageGenerationTimeout: 120,
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
