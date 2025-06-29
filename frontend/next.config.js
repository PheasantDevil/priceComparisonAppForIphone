/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // output: 'export', // Next.js 13以降では非推奨
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // 静的ファイルの出力設定
  distDir: 'out',
};

module.exports = nextConfig;
