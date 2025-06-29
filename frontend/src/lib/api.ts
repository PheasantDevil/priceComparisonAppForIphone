export type PriceInfo = {
  official_price: number;
  kaitori_price: number;
  price_diff: number;
  rakuten_diff: number;
};

export type PricesResponse = {
  series: string;
  prices: Record<string, PriceInfo>;
};

// キャッシュの型定義
type CacheEntry = {
  data: PricesResponse;
  timestamp: number;
};

// キャッシュの有効期限（5分）
const CACHE_DURATION = 5 * 60 * 1000;

// メモリキャッシュ
const cache: Record<string, CacheEntry> = {};

export async function fetchPrices(series: string): Promise<PricesResponse> {
  const url = `${
    process.env.NEXT_PUBLIC_API_URL
  }/get_prices?series=${encodeURIComponent(series)}`;

  // キャッシュをチェック
  const cached = cache[url];
  const now = Date.now();

  if (cached && now - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }

  // キャッシュがない、または期限切れの場合は新しいデータを取得
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('API fetch failed');

  const data = await res.json();

  // キャッシュを更新
  cache[url] = {
    data,
    timestamp: now,
  };

  return data;
}

// キャッシュをクリアする関数
export function clearCache() {
  Object.keys(cache).forEach(key => delete cache[key]);
}
