/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  assetPrefix:
    process.env.NODE_ENV === 'production' ? '/priceComparisonAppForIphone' : '',
  basePath:
    process.env.NODE_ENV === 'production' ? '/priceComparisonAppForIphone' : '',
  webpack: (config, { dev, isServer }) => {
    // 本番環境でのみバンドル分析を有効化
    if (!dev && !isServer) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: './bundle-analysis.html',
        })
      );
    }
    return config;
  },
};

module.exports = nextConfig;
