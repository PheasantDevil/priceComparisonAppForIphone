/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export', // Next.js 15で静的エクスポートを有効化
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // 静的エクスポート時はdistDirは不要
};

module.exports = nextConfig;
